"""Provider-only Signal Studio helpers: read-only monitoring and branded exports.

This module deliberately never sends Telegram messages or MT5 orders. The
Desktop owns those actions and passes confirmed/local records into these helpers.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
import math
import re


def _num(value):
    try:
        text = str(value if value is not None else "").replace(",", "").replace("$", "").strip()
        number = float(text)
        return number if math.isfinite(number) else None
    except Exception:
        return None


def manual_trade_mirror_key(row):
    """Stable local identity for one mirrored MT5 manual ticket (never content-based)."""
    row = row if isinstance(row, dict) else {}
    try:
        ticket = int(row.get("ticket") or row.get("order_ticket") or 0)
    except Exception:
        ticket = 0
    broker = str(row.get("broker") or "MAIN").strip().upper()
    return f"{broker}:{ticket}" if ticket > 0 else ""


def manual_trade_mirror_caption(row, state=None, destination_name=""):
    """Build a client-facing signal caption; internal MT5 volume/tickets stay private."""
    """Format a manual-only MT5 mirror post; EA/algorithm tickets fail closed."""
    row = row if isinstance(row, dict) else {}
    try:
        magic = int(row.get("magic", -1))
    except Exception:
        magic = -1
    if magic != 0:
        raise ValueError("Only manual MT5 orders with magic=0 can be mirrored.")
    symbol = str(row.get("symbol") or "UNKNOWN").strip().upper()
    direction = str(row.get("direction") or "").strip().upper()
    if direction not in ("BUY", "SELL"):
        raise ValueError("Manual MT5 order direction is unavailable.")
    kind = str(row.get("kind") or row.get("state") or "").strip().upper()
    status = str(state or row.get("state") or row.get("status") or "").strip().upper()
    raw_type = str(row.get("order_type") or "").strip().upper()
    is_open_trade = kind in ("OPEN", "LIVE") or raw_type == "MARKET"
    if is_open_trade:
        order_label = "MARKET"
        if status in ("", "LIVE", "PENDING"):
            status = "OPEN"
    else:
        order_kind = str(row.get("order_kind") or "").strip().upper()
        if order_kind in ("LIMIT", "STOP", "STOP LIMIT"):
            order_label = f"{direction} {order_kind}"
        elif raw_type and raw_type != "PENDING":
            order_label = raw_type.replace("_", " ")
        else:
            order_label = f"{direction} PENDING"
        status = status or "PENDING"
    entry = _num(row.get("entry"))
    market = _num(row.get("market_price"))
    if market is None:
        market = _num(row.get("current"))
    sl = _num(row.get("sl"))
    tp = _num(row.get("tp"))
    channel_name = str(destination_name or row.get("destination_name") or "Telegram Signals").strip()
    channel_name = channel_name[:80] or "Telegram Signals"
    def price(value):
        return "—" if value is None or abs(value) < 1e-12 else f"{value:g}"
    lines = [
        "📣 EDGEQUANT TRADE SIGNAL",
        f"{symbol} · {order_label}",
        f"ENTRY: {price(entry)}",
        f"STOP LOSS: {price(sl)}",
        f"TAKE PROFIT: {price(tp)}",
        f"STATUS: {status}",
        f"CHANNEL: {channel_name}",
        "Powered by EdgeQuant Sentinel",
    ]
    caption = "\n".join(lines)
    if len(caption.encode("utf-16-le")) // 2 > 1000:
        raise ValueError("Manual-order mirror caption exceeds Telegram's photo-caption limit.")
    return caption


def _stamp(value):
    try:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        return datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d %H:%M") if value else "-"
    except Exception:
        return "-"


def _current_events(row):
    try:
        revision = max(1, int(row.get("level_revision") or 1))
    except Exception:
        revision = 1
    out = []
    for event in row.get("progress_events") or []:
        if not isinstance(event, dict):
            continue
        try:
            event_revision = int(event.get("revision") or 1)
        except Exception:
            event_revision = 1
        if event_revision == revision:
            out.append(event)
    return out


def _tp_hits(row):
    hits = set()
    for event in _current_events(row):
        label = str(event.get("label") or "").upper()
        match = re.match(r"TP\s*(\d+)", label)
        if match and "HIT" in label:
            hits.add(int(match.group(1)))
    return hits


def monitor_transition(row, quote, now_ts=None, engine=None):
    """Compute one safe, read-only monitoring step for a published signal.

    Returns a transition dictionary. It does not mutate `row`, call MT5, edit
    Telegram, or place orders. Ambiguous first observations and long sampling
    gaps fail to REVIEW NEEDED instead of inventing an outcome.
    """
    row = row if isinstance(row, dict) else {}
    quote = quote if isinstance(quote, dict) else {}
    now_ts = float(datetime.now().timestamp() if now_ts is None else now_ts)
    state = str(row.get("status") or "PUBLISHED").upper()
    result = {"status": state, "event": "", "note": "", "quote_text": "",
              "last_mid": row.get("monitor_last_mid"),
              "last_exit": row.get("monitor_last_exit"),
              "last_exec": row.get("monitor_last_exec"),
              "last_tick_ts": row.get("monitor_last_tick_ts")}
    if not row.get("auto_progress") or str(row.get("tracking_mode") or "").upper() != "MT5_AUTO":
        result["note"] = "Manual tracking selected."
        return result
    if quote.get("error"):
        result["note"] = str(quote.get("error"))[:200]
        return result
    bid, ask = _num(quote.get("bid")), _num(quote.get("ask"))
    tick_ts = _num(quote.get("ts"))
    mid = _num(quote.get("mid"))
    if mid is None and bid is not None and ask is not None:
        mid = (bid + ask) / 2.0
    if bid is None or ask is None or bid <= 0 or ask <= 0 or mid is None or tick_ts is None:
        result["note"] = "MT5 has no valid, timestamped bid/ask quote for this symbol."
        return result
    if bool(quote.get("stale")) or tick_ts <= 0 or now_ts - tick_ts > 120.0:
        result["note"] = "Waiting for a fresh MT5 quote; the market may be closed or the terminal disconnected."
        result["quote_text"] = f"{quote.get('symbol') or ''}  {bid:g}/{ask:g}  {_stamp(tick_ts)}"
        return result
    created_ts = _num(row.get("created_ts")) or 0.0
    monitor_start_ts = _num(row.get("monitor_start_ts")) or created_ts
    if monitor_start_ts and tick_ts < monitor_start_ts - 1.0:
        result["note"] = "The latest MT5 tick predates this signal; waiting for a post-publication quote."
        return result

    composer = row.get("composer") if isinstance(row.get("composer"), dict) else {}
    direction = str(composer.get("direction") or row.get("direction") or "").upper()
    if direction not in ("BUY", "SELL"):
        result["note"] = "Signal direction is missing; automatic monitoring is paused."
        return result
    entry_a, entry_b = _num(composer.get("entry")), _num(composer.get("range_end"))
    if entry_a is None:
        result["note"] = "Signal entry is missing; automatic monitoring is paused."
        return result
    entry_low = min(entry_a, entry_b) if entry_b is not None else entry_a
    entry_high = max(entry_a, entry_b) if entry_b is not None else entry_a
    sl = _num(composer.get("sl"))
    tps = [_num(x) for x in (composer.get("tp_levels") or [])]
    tps = [x for x in tps if x is not None]
    if sl is None or not tps:
        result["note"] = "A valid SL and at least one TP are required; automatic monitoring is paused."
        return result
    pip_size = 0.0
    try:
        if engine is not None:
            pip_size = float(engine.pip_size_of(str(composer.get("symbol") or "")) or 0.0)
    except Exception:
        pip_size = 0.0
    point = _num(quote.get("point")) or 0.0
    tolerance = max(point * 1.5, pip_size * 0.1, 1e-9)
    exec_px = ask if direction == "BUY" else bid
    exit_px = bid if direction == "BUY" else ask
    result.update({"last_mid": mid, "last_exit": exit_px, "last_exec": exec_px,
                   "last_tick_ts": tick_ts,
                   "quote_text": f"{quote.get('symbol') or ''}  bid {bid:g} / ask {ask:g}  {_stamp(tick_ts)}"})

    terminal_labels = {"SL HIT", "BREAK EVEN", "CLOSED", "REVIEW NEEDED"}
    event_labels = {str(ev.get("label") or "").upper() for ev in _current_events(row)}
    if state in terminal_labels or any(label in terminal_labels for label in event_labels):
        result["note"] = f"Monitoring stopped at terminal state: {state}."
        return result

    previous_exec = _num(row.get("monitor_last_exec"))
    previous_exit = _num(row.get("monitor_last_exit"))
    previous_ts = _num(row.get("monitor_last_tick_ts"))
    if (not previous_ts and monitor_start_ts and tick_ts - monitor_start_ts > 300.0
            and state in ("RUNNING", "PENDING", "PUBLISHED", "WAITING FOR MT5", "EDITED")):
        result.update({"status": "REVIEW NEEDED", "event": "REVIEW NEEDED",
                       "note": "Automatic monitoring started more than five minutes after publication; verify missed price movement manually."})
        return result
    if previous_ts and tick_ts > previous_ts and tick_ts - previous_ts > 300.0:
        result.update({"status": "REVIEW NEEDED", "event": "REVIEW NEEDED",
                       "note": "MT5 monitoring gap exceeded five minutes; check the signal outcome manually."})
        return result

    order_type = str(composer.get("order_type") or row.get("order_type") or "LIMIT").upper()
    if order_type == "MARKET" and state not in ("RUNNING", "TP1 HIT", "TP2 HIT", "TP3 HIT", "TP4 HIT",
                                                  "TP5 HIT", "TP6 HIT", "TP7 HIT", "TP8 HIT", "TP9 HIT", "TP10 HIT"):
        state = "RUNNING"
        result.update({"status": "RUNNING", "event": "RUNNING",
                       "note": "MT5 price monitor is active; no order was placed."})
        # Establish a baseline first; do not call an already-passed TP/SL a new hit.
        return result

    if state in ("PUBLISHED", "WAITING FOR MT5", "WAITING FOR FRESH QUOTE", ""):
        state = "PENDING" if order_type != "MARKET" else "RUNNING"

    if state == "PENDING" and order_type != "MARKET":
        inside = entry_low - tolerance <= exec_px <= entry_high + tolerance
        crossed_entry = False
        if previous_exec is not None:
            crossed_entry = ((direction == "BUY" and previous_exec > entry_high + tolerance
                              and exec_px <= entry_high + tolerance) or
                             (direction == "SELL" and previous_exec < entry_low - tolerance
                              and exec_px >= entry_low - tolerance))
        if inside or crossed_entry:
            beyond_sl = (exit_px <= sl - tolerance if direction == "BUY"
                         else exit_px >= sl + tolerance)
            if beyond_sl:
                result.update({"status": "REVIEW NEEDED", "event": "REVIEW NEEDED",
                               "note": "Entry and SL may both have been crossed between MT5 observations; verify manually."})
            else:
                result.update({"status": "RUNNING", "event": "RUNNING",
                               "note": "Entry zone reached on the MT5 quote feed; monitoring only, no order was placed."})
            return result
        already_passed = ((direction == "BUY" and exec_px < entry_low - tolerance) or
                          (direction == "SELL" and exec_px > entry_high + tolerance))
        if previous_exec is None and already_passed:
            result.update({"status": "REVIEW NEEDED", "event": "REVIEW NEEDED",
                           "note": "First fresh quote is already beyond the limit-entry zone; verify whether the signal was missed."})
            return result
        result.update({"status": "PENDING", "note": "Waiting for the MT5 quote to reach the signal entry zone."})
        return result

    # Market signals and limit signals whose entry was reached are now running.
    if state == "PUBLISHED":
        state = "RUNNING"
    if state == "PENDING":
        result.update({"status": "PENDING", "note": "Waiting for entry."})
        return result
    result["status"] = "RUNNING" if state.startswith("TP") or state not in terminal_labels else state

    if previous_exit is None:
        beyond_sl_now = (exit_px <= sl - tolerance if direction == "BUY"
                         else exit_px >= sl + tolerance)
        beyond_tp_now = any((exit_px >= tp - tolerance if direction == "BUY"
                             else exit_px <= tp + tolerance) for tp in tps)
        if beyond_sl_now or beyond_tp_now:
            result.update({"status": "REVIEW NEEDED", "event": "REVIEW NEEDED",
                           "note": "First observed running quote is already beyond a terminal price level; verify manually."})
            return result
        result["note"] = "MT5 price monitoring is active; no order was placed."
        return result

    # If one observation spans both the stop and any target, ordering is unknown.
    crossed_sl = (previous_exit > sl + tolerance and exit_px <= sl - tolerance) if direction == "BUY" else (
        previous_exit < sl - tolerance and exit_px >= sl + tolerance)
    crossed_tp = any((previous_exit < tp - tolerance and exit_px >= tp + tolerance)
                     if direction == "BUY" else
                     (previous_exit > tp + tolerance and exit_px <= tp - tolerance)
                     for tp in tps)
    if crossed_sl and crossed_tp:
        result.update({"status": "REVIEW NEEDED", "event": "REVIEW NEEDED",
                       "note": "MT5 sampling crossed both SL and TP between observations; outcome ordering is uncertain."})
        return result
    sl_hit = exit_px <= sl - tolerance if direction == "BUY" else exit_px >= sl + tolerance
    if sl_hit:
        result.update({"status": "SL HIT", "event": "SL HIT",
                       "note": "Signal SL level reached on the MT5 quote feed; this is signal tracking, not an MT5 position result."})
        return result

    try:
        already_tp = max(_tp_hits(row) or {0})
    except Exception:
        already_tp = 0
    reached = max((i for i, tp in enumerate(tps, 1)
                   if (exit_px >= tp - tolerance if direction == "BUY"
                       else exit_px <= tp + tolerance)), default=0)
    reached = max(reached, already_tp)
    if reached > already_tp:
        final = reached >= len(tps)
        result.update({"status": "CLOSED" if final else "RUNNING",
                       "event": f"TP{reached} HIT",
                       "note": f"TP{reached} reached on the MT5 quote feed; no order was placed."})
        return result

    advice = str(composer.get("be_advice") or "").upper()
    be_match = re.search(r"AFTER\s+TP\s*(\d+)", advice)
    if be_match and re.search(r"\b(?:ENTRY|BREAK\s*EVEN|BE)\b", advice):
        be_after = int(be_match.group(1))
        if already_tp >= be_after:
            returned_to_entry = (exit_px <= entry_high + tolerance if direction == "BUY"
                                 else exit_px >= entry_low - tolerance)
            if returned_to_entry:
                result.update({"status": "BREAK EVEN", "event": "BREAK EVEN",
                               "note": "Price returned to the advised break-even entry after the configured TP; verify the actual trade manually."})
                return result
    result["note"] = "MT5 price monitoring is active; no order was placed."
    return result


def _publication_report_row(row, trades_by_id, engine):
    row = row if isinstance(row, dict) else {}
    composer = row.get("composer") if isinstance(row.get("composer"), dict) else {}
    events = _current_events(row)
    hits = sorted(_tp_hits(row))
    tps = [_num(x) for x in (composer.get("tp_levels") or [])]
    tps = [x for x in tps if x is not None]
    entry_a, entry_b = _num(composer.get("entry")), _num(composer.get("range_end"))
    entry = ((entry_a + entry_b) / 2.0 if entry_a is not None and entry_b is not None
             else entry_a)
    symbol = str(composer.get("symbol") or row.get("symbol") or "")
    direction = str(composer.get("direction") or row.get("direction") or "").upper()
    sign = -1.0 if direction == "SELL" else 1.0
    try:
        pip = float(engine.pip_size_of(symbol) or 0.0) if engine is not None else 0.0
    except Exception:
        pip = 0.0
    status = str(row.get("status") or "PUBLISHED").upper()
    sl = _num(composer.get("sl"))
    nominal = None
    if entry is not None and pip > 0:
        if status == "BREAK EVEN":
            nominal = 0.0
        elif "SL HIT" in status and sl is not None:
            nominal = (sl - entry) / pip * sign
        elif hits and tps:
            idx = min(max(hits), len(tps)) - 1
            nominal = (tps[idx] - entry) / pip * sign

    local_linked_ids = [str(x) for x in (row.get("local_trade_ids") or [])]
    manual_linked_ids = [str(x) for x in (row.get("provider_manual_trade_ids") or [])]
    linked_ids = list(dict.fromkeys(local_linked_ids + manual_linked_ids))
    linked = [trades_by_id[x] for x in linked_ids if x in trades_by_id]
    closed = [t for t in linked if str(t.get("status") or "").lower() == "closed"]
    actual_net_values = []
    actual_pips_values = []
    for trade in closed:
        try:
            if trade.get("net") is not None:
                actual_net_values.append(float(trade.get("net") or 0.0))
        except Exception:
            pass
        if (trade.get("close_price") not in (None, "", 0, 0.0)
                and (trade.get("open_price") or trade.get("price"))):
            try:
                actual_pips_values.append(float(engine.jr_trade_pips(trade)))
            except Exception:
                pass
    actual_net = sum(actual_net_values) if actual_net_values else None
    actual_pips = sum(actual_pips_values) if actual_pips_values else None
    terminal_linked = bool(linked) and all(
        str(t.get("status") or "").lower() in ("closed", "cancelled", "rejected") for t in linked)
    if terminal_linked and actual_net is not None:
        outcome = "WIN" if actual_net > 1e-9 else ("LOSS" if actual_net < -1e-9 else "BE")
    elif "REVIEW NEEDED" in status:
        outcome = "REVIEW"
    elif "SL HIT" in status:
        outcome = "LOSS"
    elif "BREAK EVEN" in status or status == "BE":
        outcome = "BE"
    elif status == "CLOSED" and hits:
        outcome = "WIN"
    elif tps and hits and max(hits) >= len(tps) and status.startswith("TP"):
        outcome = "WIN"
    else:
        outcome = "OPEN"
    targets = list(row.get("targets") or [])
    try:
        created_ts = float(row.get("created_ts") or 0.0)
    except Exception:
        created_ts = 0.0
    entry_text = str(composer.get("entry") or "-")
    if str(composer.get("entry_mode") or "").upper() == "RANGE" and composer.get("range_end"):
        entry_text += " - " + str(composer.get("range_end"))
    return {"id": str(row.get("id") or ""), "created_ts": created_ts,
            "created": _stamp(created_ts), "symbol": symbol, "direction": direction,
            "order_type": str(composer.get("order_type") or row.get("order_type") or "LIMIT").upper(),
            "entry": entry_text, "sl": str(composer.get("sl") or "-"),
            "tps": ", ".join(str(x) for x in (composer.get("tp_levels") or [])) or "-",
            "status": status, "outcome": outcome,
            "sl_hit": ("SL HIT" in status or any(
                "SL HIT" in str(ev.get("label") or "").upper() for ev in events)),
            "tracking": ("MT5 AUTO (read-only)" if str(row.get("tracking_mode") or "").upper() == "MT5_AUTO"
                         else ("LINKED JOURNAL AUTO" if row.get("auto_progress") else "MANUAL")),
            "tp_hits": hits, "tp_count": len(tps), "targets": len(targets),
            "destination_names": [str(x.get("name") or x.get("id") or "") for x in targets],
            "local_trade_ids": local_linked_ids,
            "provider_manual_trade_ids": manual_linked_ids,
            "linked_trade_ids": linked_ids, "actual_net": actual_net,
            "actual_pips": actual_pips, "nominal_pips": nominal,
            "best_tp": max(hits) if hits else 0,
            "last_price": row.get("monitor_last_mid"),
            "last_quote": str(row.get("monitor_quote_text") or ""),
            "monitor_note": str(row.get("monitor_note") or ""),
            "actual_trade_count": len(closed)}


def provider_signal_rows(publications, trades=None, engine=None):
    trades_by_id = {str(t.get("id")): t for t in (trades or [])
                    if isinstance(t, dict) and t.get("id") is not None}
    out = [_publication_report_row(row, trades_by_id, engine)
           for row in (publications or []) if isinstance(row, dict)]
    out.sort(key=lambda r: r.get("created_ts") or 0, reverse=True)
    return out


def _periods(now=None):
    if now is None:
        now = datetime.now()
    elif not isinstance(now, datetime):
        now = datetime.fromtimestamp(float(now))
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week = today - timedelta(days=today.weekday())
    month = today.replace(day=1)
    return {"today": (today.timestamp(), "TODAY"),
            "week": (week.timestamp(), "THIS WEEK"),
            "month": (month.timestamp(), "THIS MONTH"),
            "all": (None, "ALL TIME")}, now.timestamp()


def _summarize_rows(rows, label):
    summary = {"label": label, "signals": len(rows), "wins": 0, "losses": 0,
               "be": 0, "decided": 0, "win_rate": None, "tp_levels": {},
               "actual_trades": 0, "actual_net": None, "actual_pips": None,
               "actual_pips_won": None, "actual_pips_lost": None,
               "nominal_pips": None, "nominal_pips_won": None,
               "nominal_pips_lost": None, "best_signal": None}
    nets, actual_pips, nominal_pips = [], [], []
    actual_wins, actual_losses, nominal_wins, nominal_losses = [], [], [], []
    best_actual, best_nominal = [], []
    for row in rows:
        outcome = row.get("outcome")
        if outcome == "WIN":
            summary["wins"] += 1
        elif outcome == "LOSS":
            summary["losses"] += 1
        elif outcome == "BE":
            summary["be"] += 1
        for index in row.get("tp_hits") or []:
            summary["tp_levels"][int(index)] = summary["tp_levels"].get(int(index), 0) + 1
        if row.get("actual_net") is not None:
            nets.append(float(row["actual_net"]))
            best_actual.append(row)
        if row.get("actual_pips") is not None:
            pips = float(row["actual_pips"])
            actual_pips.append(pips)
            if pips > 0:
                actual_wins.append(pips)
            elif pips < 0:
                actual_losses.append(pips)
        if row.get("nominal_pips") is not None:
            pips = float(row["nominal_pips"])
            nominal_pips.append(pips)
            if pips > 0:
                nominal_wins.append(pips)
            elif pips < 0:
                nominal_losses.append(pips)
            best_nominal.append(row)
        summary["actual_trades"] += int(row.get("actual_trade_count") or 0)
    summary["decided"] = summary["wins"] + summary["losses"] + summary["be"]
    decisive = summary["wins"] + summary["losses"]
    summary["win_rate"] = (100.0 * summary["wins"] / decisive) if decisive else None
    if nets:
        summary["actual_net"] = sum(nets)
    if actual_pips:
        summary["actual_pips"] = sum(actual_pips)
        summary["actual_pips_won"] = sum(actual_wins)
        summary["actual_pips_lost"] = sum(actual_losses)
    if nominal_pips:
        summary["nominal_pips"] = sum(nominal_pips)
        summary["nominal_pips_won"] = sum(nominal_wins)
        summary["nominal_pips_lost"] = sum(nominal_losses)
    if best_actual:
        summary["best_signal"] = max(best_actual, key=lambda r: float(r.get("actual_net") or 0.0))
        summary["best_basis"] = "actual net USD"
    elif best_nominal:
        summary["best_signal"] = max(best_nominal, key=lambda r: float(r.get("nominal_pips") or 0.0))
        summary["best_basis"] = "nominal signal pips"
    else:
        summary["best_basis"] = "not recorded"
    return summary


def _pips_wl_label(summary, prefix="actual"):
    if summary.get(f"{prefix}_pips") is None:
        return "Not recorded"
    won = float(summary.get(f"{prefix}_pips_won") or 0.0)
    lost = float(summary.get(f"{prefix}_pips_lost") or 0.0)
    return f"{won:+,.1f} / {lost:+,.1f}"


def _destination_breakdown(rows, since=None, until=None):
    """Count publications and outcomes per destination without duplicating P&L."""
    groups = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        try:
            created = float(row.get("created_ts") or 0.0)
        except Exception:
            created = 0.0
        if since is not None and created < float(since):
            continue
        if until is not None and created > float(until):
            continue
        names = list(dict.fromkeys(str(x).strip() for x in
                                   (row.get("destination_names") or []) if str(x).strip()))
        if not names:
            continue
        order_type = "MARKET" if str(row.get("order_type") or "LIMIT").upper() == "MARKET" else "LIMIT"
        outcome = str(row.get("outcome") or "OPEN").upper()
        for name in names:
            item = groups.setdefault(name, {"destination": name, "signals": 0,
                "actual_trades": 0, "market": 0, "limit": 0, "wins": 0,
                "losses": 0, "be": 0, "tp_hits": 0, "sl_hits": 0})
            item["signals"] += 1
            try:
                item["actual_trades"] += int(row.get("actual_trade_count") or 0)
            except Exception:
                pass
            item[order_type.lower()] += 1
            if outcome == "WIN":
                item["wins"] += 1
            elif outcome == "LOSS":
                item["losses"] += 1
            elif outcome == "BE":
                item["be"] += 1
            item["tp_hits"] += len(row.get("tp_hits") or [])
            if row.get("sl_hit"):
                item["sl_hits"] += 1
    return sorted(groups.values(), key=lambda item: (-item["signals"],
                                                      item["destination"].casefold()))


def provider_performance(publications, trades=None, engine=None, now=None):
    rows = provider_signal_rows(publications, trades, engine)
    periods, end_ts = _periods(now)
    summaries = {}
    for key, (start_ts, label) in periods.items():
        picked = [row for row in rows if row.get("created_ts")
                  and (start_ts is None or row["created_ts"] >= start_ts)
                  and row["created_ts"] <= end_ts]
        summaries[key] = _summarize_rows(picked, label)
    today_start = periods["today"][0]
    return {"rows": rows, "periods": summaries,
            "groups": _destination_breakdown(rows),
            "today_groups": _destination_breakdown(rows, today_start, end_ts)}


def _logo_assets(logo_path):
    """Convert a custom uploaded logo into PDF JPEG and Excel PNG assets."""
    if not logo_path or not Path(str(logo_path)).is_file():
        return None, 0, None
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError(
            "Pillow could not be loaded to embed the uploaded logo in PDF/Excel exports. "
            f"Import diagnostic: {type(exc).__name__}: {exc}. "
            "For the Windows app, rebuild the complete folder with the current BUILD-EXE.bat "
            "and use dist/EdgeQuantSentinel; the standalone EXE is not sufficient.") from exc
    try:
        with Image.open(str(logo_path)) as source:
            original = source.convert("RGBA")
        # PDF renderer supports a single JPEG XObject, so use a padded square.
        square = Image.new("RGBA", (240, 240), (255, 255, 255, 255))
        fitted = original.copy()
        fitted.thumbnail((224, 224), Image.Resampling.LANCZOS)
        square.alpha_composite(fitted, ((240 - fitted.width) // 2, (240 - fitted.height) // 2))
        jpeg_buf = BytesIO()
        square.convert("RGB").save(jpeg_buf, "JPEG", quality=90, optimize=True)
        # Excel image preserves a landscape-friendly brand lockup.
        landscape = Image.new("RGBA", (480, 200), (255, 255, 255, 255))
        fitted2 = original.copy()
        fitted2.thumbnail((460, 180), Image.Resampling.LANCZOS)
        landscape.alpha_composite(fitted2, ((480 - fitted2.width) // 2,
                                             (200 - fitted2.height) // 2))
        png_buf = BytesIO()
        landscape.save(png_buf, "PNG", optimize=True)
        return jpeg_buf.getvalue(), 240, png_buf.getvalue()
    except Exception as exc:
        raise RuntimeError(
            "The selected provider logo could not be decoded by Pillow. "
            f"Image diagnostic: {type(exc).__name__}: {exc}. "
            "Verify the logo is a valid PNG/JPEG; if this is the Windows app, rebuild "
            "with BUILD-EXE.bat and keep the complete dist/EdgeQuantSentinel folder.") from exc


def _excel_logo(ws, png, cell="N1"):
    if not png:
        return None
    try:
        from openpyxl.drawing.image import Image as XLImage
        stream = BytesIO(png)
        image = XLImage(stream)
        image.width, image.height = 160, 67
        ws.add_image(image, cell)
        return stream
    except Exception as exc:
        raise RuntimeError(f"Excel could not embed the provider logo: {exc}") from exc


def _style_sheet(ws, header_row=1):
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    navy = "101620"
    gold = "E3B341"
    thin = Side(style="thin", color="D8DEE8")
    for cell in ws[header_row]:
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.font = Font(name="Aptos", bold=True, color="FFFFFF", size=10)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = Border(bottom=thin)
    ws.row_dimensions[header_row].height = 24
    for row in ws.iter_rows(min_row=header_row + 1):
        for cell in row:
            cell.font = Font(name="Aptos", color="253247", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = f"A{header_row + 1}"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    return gold




def _filter_publications_for_destination(publications, trades, destination_id,
                                         destination_name="", start_ts=None, end_ts=None,
                                         require_message_id=False):
    """Return only successful/publication rows for one Telegram destination and time window."""
    try:
        wanted_id = int(destination_id)
    except Exception:
        wanted_id = None
    wanted_name = str(destination_name or "").strip().casefold()
    selected = []
    linked_ids = set()
    for original in publications or []:
        if not isinstance(original, dict):
            continue
        try:
            created = float(original.get("created_ts") or 0.0)
        except Exception:
            continue
        if start_ts is not None and created < float(start_ts):
            continue
        if end_ts is not None and created > float(end_ts):
            continue
        matched_targets = []
        for target in original.get("targets") or []:
            if not isinstance(target, dict):
                continue
            try:
                target_id = int(target.get("id"))
            except Exception:
                target_id = None
            matches = (wanted_id is not None and target_id == wanted_id)
            if wanted_id is None and wanted_name:
                matches = str(target.get("name") or "").strip().casefold() == wanted_name
            if not matches:
                continue
            if require_message_id:
                try:
                    if int(target.get("message_id") or 0) <= 0:
                        continue
                except Exception:
                    continue
            matched_targets.append(dict(target))
        if not matched_targets:
            continue
        row = dict(original)
        row["targets"] = matched_targets
        selected.append(row)
        for trade_id in (list(row.get("local_trade_ids") or []) +
                         list(row.get("provider_manual_trade_ids") or [])):
            if trade_id is not None:
                linked_ids.add(str(trade_id))
    trade_rows = [dict(row) for row in (trades or [])
                  if isinstance(row, dict) and str(row.get("id")) in linked_ids]
    selected.sort(key=lambda row: float(row.get("created_ts") or 0.0))
    trade_rows.sort(key=lambda row: float(row.get("placed_ts") or 0.0))
    return selected, trade_rows


def _set_software_footer(workbook):
    """Put the EdgeQuant Sentinel software credit at bottom-left on printed sheets."""
    for ws in workbook.worksheets:
        footer = ws.oddFooter.left
        footer.text = "EdgeQuant Sentinel"
        footer.size = 8
        footer.font = "Arial,Regular"
        footer.color = "667085"

def _linked_trade_journal_entries(signal_rows, trades, engine=None):
    """Build one report row per signal-to-journal-trade link; never invent unlinked trades."""
    trade_by_id = {str(row.get("id")): row for row in (trades or [])
                   if isinstance(row, dict) and row.get("id") is not None}
    entries = []
    for signal in signal_rows or []:
        for trade_id in signal.get("linked_trade_ids") or signal.get("local_trade_ids") or []:
            trade = trade_by_id.get(str(trade_id))
            if trade is None:
                continue
            try:
                pips = engine.jr_trade_pips(trade) if engine is not None else None
            except Exception:
                pips = None
            entries.append({"signal_id": str(signal.get("id") or ""),
                            "signal": f"{signal.get('symbol', '')} {signal.get('direction', '')}".strip(),
                            "trade_id": str(trade_id), "trade": trade, "pips": pips})
    entries.sort(key=lambda item: float(item["trade"].get("placed_ts") or 0.0))
    return entries


def _pdf_linked_trade_journal(pdf, signal_rows, trades, engine=None, page_size=25):
    """Append a readable, per-signal linked MT5 trade journal to a Provider PDF."""
    entries = _linked_trade_journal_entries(signal_rows, trades, engine)
    pages = [entries[offset:offset + page_size] for offset in range(0, len(entries), page_size)] or [[]]
    for page_index, page_rows in enumerate(pages):
        pdf.new_page()
        right = (f"{page_index * page_size + 1}-{page_index * page_size + len(page_rows)} / {len(entries)}"
                 if page_rows else "NO LINKED MT5 TRADES")
        y = pdf.header("LINKED MT5 TRADE JOURNAL", right=right)
        y = pdf.section(y, "TRADES LINKED TO PROVIDER SIGNALS",
                        "closed/open broker journal rows; no unlinked trades are added")
        if page_rows:
            table_rows = []
            colors = []
            for item in page_rows:
                trade = item["trade"]
                entry_px = trade.get("open_price", trade.get("price"))
                close_px = trade.get("close_price")
                price_path = f"{entry_px if entry_px is not None else '-'} → {close_px if close_px is not None else '-'}"
                net = trade.get("net")
                try:
                    net_number = float(net) if net is not None else None
                except Exception:
                    net_number = None
                table_rows.append([
                    item["signal_id"][-10:], item["trade_id"],
                    _stamp(trade.get("placed_ts")),
                    item["signal"],
                    f"{trade.get('status') or '-'} / {trade.get('result') or '-'}",
                    price_path,
                    "-" if item.get("pips") is None else f"{float(item['pips']):+.1f}",
                    "-" if net_number is None else f"{net_number:+.2f}",
                    str(trade.get("ticket") or "-")])
                colors.append(pdf.T("green") if net_number is not None and net_number > 0 else
                              (pdf.T("red") if net_number is not None and net_number < 0 else None))
            y = _pdf_table(pdf, y, table_rows,
                ["SIGNAL ID", "TRADE ID", "PLACED", "SIGNAL", "STATUS / RESULT", "ENTRY → EXIT", "PIPS", "NET", "TICKET"],
                [58, 62, 65, 66, 70, 74, 42, 47, 43], colors, row_h=19, color_col=7)
            pdf.text(40, 46, "Trade rows are shown only when linked to a Provider signal; NET uses recorded journal currency.",
                     1, 6.0, pdf.T("muted"))
        else:
            pdf.text(40, y, "No linked MT5 Trade Journal rows are recorded for these signals. "
                             "Published signals are still listed above; this is not fabricated broker history.",
                     1, 7.5, pdf.T("muted"))
            pdf.text(40, 46, "Link/record an MT5 trade before expecting actual broker execution outcomes.",
                     1, 6.0, pdf.T("muted"))
        pdf.footer()


def export_provider_xlsx(path, publications, trades=None, engine=None, logo_path="",
                         provider_name="Signal Provider", plan=None,
                         destination_id=None, destination_name="", start_ts=None,
                         end_ts=None, require_message_id=False, report_now=None,
                         daily_report=False):
    """Create an editable, logo-branded provider performance workbook."""
    try:
        from openpyxl import Workbook
        from openpyxl.chart import BarChart, Reference
        from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except Exception as exc:
        raise RuntimeError(
            "openpyxl is required for the branded Excel report; install openpyxl. "
            f"Import diagnostic: {type(exc).__name__}: {exc}. "
            "If this is the packaged app, rebuild with the current BUILD-EXE.bat.") from exc
    if destination_id is not None or start_ts is not None or end_ts is not None:
        publications, trades = _filter_publications_for_destination(
            publications, trades, destination_id, destination_name,
            start_ts=start_ts, end_ts=end_ts, require_message_id=require_message_id)
    if destination_id is not None:
        provider_name = str(destination_name or provider_name or "Signal Provider")
    if daily_report and report_now is None:
        report_now = datetime.now().astimezone()
    data = provider_performance(publications, trades, engine, now=report_now)
    summaries = data["periods"]
    rows = data["rows"]
    jpeg, px, png = _logo_assets(logo_path)
    wb = Workbook()
    wb.properties.creator = str(provider_name or "Signal Provider")
    wb.properties.title = (f"{provider_name} Daily Signal Report {report_now:%Y-%m-%d}"
                           if daily_report else f"{provider_name} Provider Performance")
    ws = wb.active
    ws.title = "SUMMARY"
    max_col = 26
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=12)
    ws.cell(1, 1, str(provider_name or "Signal Provider"))
    ws.cell(1, 1).font = Font(name="Aptos Display", size=22, bold=True, color="E3B341")
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=12)
    ws.cell(2, 1, (f"Daily Provider Signal Report • {report_now:%Y-%m-%d} • generated "
                   f"{datetime.now().strftime('%H:%M')}" if daily_report else
                   "Provider Signal Performance • generated " + datetime.now().strftime("%Y-%m-%d %H:%M")))
    ws.cell(2, 1).font = Font(name="Aptos", size=10, color="667085")
    logo_stream = _excel_logo(ws, png, "N1")
    headers = (["PERIOD", "SIGNALS", "WINS", "LOSSES", "BE", "DECIDED",
                "WIN RATE %"] + [f"TP{i} HITS" for i in range(1, 11)] +
               ["ACTUAL MT5 PIPS", "ACTUAL NET USD", "NOMINAL SIGNAL PIPS",
                "ACTUAL PIPS WON", "ACTUAL PIPS LOST",
                "NOMINAL PIPS WON", "NOMINAL PIPS LOST", "BEST SIGNAL", "BEST BASIS"])
    header_row = 4
    for col, value in enumerate(headers, 1):
        ws.cell(header_row, col, value)
    period_keys = ("today",) if daily_report else ("today", "week", "month", "all")
    for row_index, key in enumerate(period_keys, header_row + 1):
        item = summaries[key]
        values = [item["label"], item["signals"], item["wins"], item["losses"], item["be"],
                  item["decided"], item["win_rate"]]
        values += [item["tp_levels"].get(i, 0) for i in range(1, 11)]
        values += [item["actual_pips"], item["actual_net"], item["nominal_pips"],
                   item["actual_pips_won"], item["actual_pips_lost"],
                   item["nominal_pips_won"], item["nominal_pips_lost"]]
        best = item.get("best_signal") or {}
        values += [f"{best.get('symbol', '')} {best.get('direction', '')}".strip() or None,
                   item.get("best_basis")]
        for col, value in enumerate(values, 1):
            ws.cell(row_index, col, value)
    gold = _style_sheet(ws, header_row)
    last_summary_row = header_row + len(period_keys)
    for row in ws.iter_rows(min_row=header_row + 1, max_row=last_summary_row):
        for cell in row:
            if cell.column >= 18 and isinstance(cell.value, (int, float)):
                cell.number_format = '#,##0.00;[Red]-#,##0.00'
        if isinstance(row[6].value, (int, float)):
            row[6].number_format = '0.0"%"'
    for col in range(1, max_col + 1):
        ws.column_dimensions[get_column_letter(col)].width = 15
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["G"].width = 14
    ws.column_dimensions["R"].width = 17
    ws.column_dimensions["S"].width = 18
    ws.column_dimensions["T"].width = 20
    ws.column_dimensions["Y"].width = 24
    ws.column_dimensions["Z"].width = 24
    ws.conditional_formatting.add(f"G5:G{last_summary_row}", ColorScaleRule(
        start_type="num", start_value=0, start_color="FFFF8A8A",
        mid_type="num", mid_value=50, mid_color="FFFFE08A",
        end_type="num", end_value=100, end_color="FF7ED694"))
    ws.conditional_formatting.add(f"R5:X{last_summary_row}", DataBarRule(start_type="min", end_type="max", color="FF4EA8DE"))
    ws["A11"] = "DATA NOTE"
    ws["A11"].font = Font(bold=True, color="101620")
    ws.merge_cells("A12:X13")
    ws["A12"] = ("Actual MT5 pips and USD include only closed, linked local journal trades. "
                  "Nominal signal pips are price-distance estimates to recorded levels, not broker-confirmed profit. "
                  "Signals are grouped by publication date; no outcomes are fabricated for pending or open signals.")
    ws["A12"].alignment = Alignment(wrap_text=True, vertical="top")
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Signals for the day" if daily_report else "Signals by period"
    chart.y_axis.title = "Signal count"
    chart.x_axis.title = "Period"
    chart.add_data(Reference(ws, min_col=2, min_row=header_row, max_row=last_summary_row), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=header_row + 1, max_row=last_summary_row))
    chart.height, chart.width = 7.0, 15.0
    ws.add_chart(chart, "A15")

    sig = wb.create_sheet("SIGNALS")
    sig.merge_cells("A1:W1")
    sig["A1"] = "PUBLISHED SIGNAL DETAIL"
    sig["A1"].font = Font(name="Aptos Display", size=17, bold=True, color="E3B341")
    signal_headers = ["SIGNAL ID", "CREATED", "SYMBOL", "DIRECTION", "ENTRY", "SL", "TAKE PROFITS",
                      "STATUS", "OUTCOME", "TRACKING", "TP LEVELS HIT", "DESTINATIONS",
                      "LAST MT5 PRICE", "LAST MT5 QUOTE", "MONITOR NOTE", "LINKED MT5 TRADE IDS",
                      "ACTUAL PIPS", "ACTUAL NET USD", "NOMINAL SIGNAL PIPS", "BEST TP", "DESTINATION COUNT",
                      "ORDER TYPE", "SL HIT"]
    for col, value in enumerate(signal_headers, 1):
        sig.cell(3, col, value)
    for r_index, item in enumerate(rows, 4):
        values = [item["id"], item["created"], item["symbol"], item["direction"], item["entry"],
                  item["sl"], item["tps"], item["status"], item["outcome"], item["tracking"],
                  ", ".join(f"TP{i}" for i in item["tp_hits"]) or "-",
                  ", ".join(item["destination_names"]) or "-", item["last_price"], item["last_quote"],
                  item["monitor_note"], ", ".join(item.get("linked_trade_ids") or item["local_trade_ids"]) or "-",
                  item["actual_pips"], item["actual_net"], item["nominal_pips"], item["best_tp"],
                  item["targets"], item["order_type"], "YES" if item.get("sl_hit") else "NO"]
        for col, value in enumerate(values, 1):
            sig.cell(r_index, col, value)
    _style_sheet(sig, 3)
    widths = [20, 18, 12, 12, 18, 15, 24, 20, 14, 24, 18, 36, 18, 20, 42, 28, 16, 18, 22, 12, 18, 14, 12]
    for col, width in enumerate(widths, 1):
        sig.column_dimensions[sig.cell(3, col).column_letter].width = width
    sig.auto_filter.ref = f"A3:W{max(3, 3 + len(rows))}"
    for row in sig.iter_rows(min_row=4, max_row=3 + len(rows)):
        for cell in row:
            if cell.column in (11, 12, 13, 14) and isinstance(cell.value, (int, float)):
                cell.number_format = '#,##0.00;[Red]-#,##0.00'

    destinations_sheet = wb.create_sheet("DESTINATIONS")
    destination_headers = ["DESTINATION", "SIGNALS", "LINKED MT5 TRADES", "MARKET", "LIMIT", "WINS",
                           "LOSSES", "BREAK EVEN", "TP LEVEL HITS", "SL HITS"]
    for col, value in enumerate(destination_headers, 1):
        destinations_sheet.cell(1, col, value)
    destination_rows = data.get("groups") or _destination_breakdown(rows)
    for r_index, item in enumerate(destination_rows, 2):
        values = [item.get("destination"), item.get("signals", 0), item.get("actual_trades", 0),
                  item.get("market", 0), item.get("limit", 0), item.get("wins", 0),
                  item.get("losses", 0), item.get("be", 0), item.get("tp_hits", 0),
                  item.get("sl_hits", 0)]
        for col, value in enumerate(values, 1):
            destinations_sheet.cell(r_index, col, value)
    _style_sheet(destinations_sheet, 1)
    for col, width in enumerate([34, 14, 19, 14, 14, 12, 12, 16, 18, 12], 1):
        destinations_sheet.column_dimensions[destinations_sheet.cell(1, col).column_letter].width = width
    destinations_sheet.auto_filter.ref = f"A1:J{max(1, 1 + len(destination_rows))}"

    trades_sheet = wb.create_sheet("LINKED MT5 TRADES")
    trade_headers = ["SIGNAL ID", "SIGNAL SYMBOL / DIR", "TRADE ID", "PLACED", "CLOSED", "BROKER",
                     "SYMBOL", "DIRECTION", "STATUS", "RESULT", "ENTRY PRICE", "CLOSE PRICE",
                     "PIPS", "NET", "TICKET", "TAG"]
    for col, value in enumerate(trade_headers, 1):
        trades_sheet.cell(1, col, value)
    linked_entries = _linked_trade_journal_entries(rows, trades, engine)
    linked_trade_rows = [item["trade"] for item in linked_entries]
    for r_index, item in enumerate(linked_entries, 2):
        trade = item["trade"]
        values = [item["signal_id"], item["signal"], item["trade_id"],
                  _stamp(trade.get("placed_ts")), _stamp(trade.get("closed_ts")),
                  trade.get("broker"), trade.get("symbol"), trade.get("direction"),
                  trade.get("status"), trade.get("result"),
                  trade.get("open_price", trade.get("price")), trade.get("close_price"),
                  item.get("pips"), trade.get("net"), trade.get("ticket"), trade.get("tag")]
        for col, value in enumerate(values, 1):
            trades_sheet.cell(r_index, col, value)
    if not linked_entries:
        trades_sheet.merge_cells("A2:P2")
        trades_sheet["A2"] = "No linked MT5 Trade Journal rows are recorded for the selected Provider signals."
    _style_sheet(trades_sheet, 1)
    for col, width in enumerate([24, 24, 22, 18, 18, 18, 13, 12, 15, 14, 18, 18, 14, 16, 18, 18], 1):
        trades_sheet.column_dimensions[trades_sheet.cell(1, col).column_letter].width = width
    trades_sheet.auto_filter.ref = f"A1:P{max(2, 1 + len(linked_trade_rows))}"

    if plan:
        _add_plan_sheets(wb, plan, png, logo_streams=[])
    _set_software_footer(wb)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(path))
    # Keep the image stream alive until serialization is complete.
    _ = logo_stream
    return path


def export_provider_daily_xlsx(path, publications, trades=None, engine=None, logo_path="",
                               destination_id=None, destination_name="", now=None):
    """Create an editable destination-branded workbook with only today's successfully sent signals."""
    now = now if isinstance(now, datetime) else (datetime.fromtimestamp(float(now)).astimezone()
                                                   if now is not None else datetime.now().astimezone())
    if now.tzinfo is None:
        now = now.astimezone()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    end = now.timestamp()
    name = str(destination_name or destination_id or "Telegram destination").strip()
    daily_publications, daily_trades = _filter_publications_for_destination(
        publications, trades, destination_id, name, start_ts=start, end_ts=end,
        require_message_id=True)
    if not daily_publications:
        raise RuntimeError(f"No successfully sent Provider signals for {name} on {now:%Y-%m-%d}.")
    return export_provider_xlsx(
        path, daily_publications, trades=daily_trades, engine=engine,
        logo_path=logo_path, provider_name=name, destination_id=destination_id,
        destination_name=name, require_message_id=True, report_now=now, daily_report=True)


def _add_plan_sheets(wb, plan, png=None, logo_streams=None):
    from openpyxl.styles import Alignment, Font, PatternFill
    inputs = wb.create_sheet("PLAN INPUTS")
    inputs.merge_cells("A1:D1")
    inputs["A1"] = "EDITABLE TRADING PLAN INPUTS"
    inputs["A1"].font = Font(name="Aptos Display", size=17, bold=True, color="E3B341")
    stream = _excel_logo(inputs, png, "F1") if png else None
    if logo_streams is not None and stream is not None:
        logo_streams.append(stream)
    input_rows = [
        ("Starting capital (USD)", plan.get("capital")),
        ("Trading days", plan.get("days")),
        ("Months", plan.get("months")),
        ("Risk per trade (%)", plan.get("risk_pct")),
        ("Monthly target (%)", plan.get("target_pct")),
        ("Win rate used (%)", plan.get("win")),
        ("Reward : risk", plan.get("rr")),
        ("Signals per day", plan.get("trades_day")),
        ("Risk per trade (USD)", plan.get("risk_usd")),
        ("Expected P/L per day (USD)", plan.get("per_day")),
        ("Expected P/L per month (USD)", plan.get("per_month")),
        ("Plan cadence", plan.get("per")),
    ]
    target_state = plan.get("daily_target_status") if isinstance(plan.get("daily_target_status"), dict) else {}
    target_actual = _num(target_state.get("net"))
    target_goal = _num(target_state.get("target"))
    target_pct = _num(target_state.get("done_pct"))
    target_remaining = _num(target_state.get("remaining"))
    target_achieved = bool(target_state.get("achieved"))
    input_rows.extend([
        ("Today's realized P/L (USD)", target_actual),
        ("Today's target (USD)", target_goal),
        ("Today's target completion (%)", target_pct),
        ("Today's remaining (USD)", target_remaining),
        ("Today's target achieved", "YES" if target_achieved else "NO"),
    ])
    inputs.append(["INPUT", "VALUE"])
    for item in input_rows:
        inputs.append(list(item))
    _style_sheet(inputs, 2)
    inputs.column_dimensions["A"].width = 35
    inputs.column_dimensions["B"].width = 22
    note_row = 4 + len(input_rows)
    inputs.cell(note_row, 1, "Projection note")
    inputs.cell(note_row, 1).font = Font(bold=True, color="101620")
    inputs.merge_cells(start_row=note_row + 1, start_column=1,
                       end_row=note_row + 2, end_column=4)
    inputs.cell(note_row + 1, 1, ("The projection is illustrative, not financial advice or a promise. "
                      "Projection cells are editable; change the rate in the day-by-day plan sheet and Excel recalculates balances. "
                      "Edit inputs in the app and regenerate to recompute risk/expectancy."))
    inputs.cell(note_row + 1, 1).alignment = Alignment(wrap_text=True, vertical="top")

    projection_title = "DAY-BY-DAY PLAN" if str(plan.get("per") or "DAYS").upper() == "DAYS" else "MONTHLY PROJECTION"
    projection = wb.create_sheet(projection_title)
    headers = ["DAY / MONTH", "PERIOD COUNT", "START BALANCE USD", "GAIN USD", "END BALANCE USD",
               "RATE % PER PERIOD", "TARGET HIT"]
    for col, value in enumerate(headers, 1):
        projection.cell(1, col, value)
    cadence = str(plan.get("per") or "DAYS").upper()
    base_rate = float(plan.get("day_pct") or 0.0) if cadence == "DAYS" else float(plan.get("month_pct") or 0.0)
    for index, item in enumerate(plan.get("table") or [], 2):
        step_count = max(1, int(item.get("days") or 1)) if cadence == "DAYS" else 1
        projection.cell(index, 1, item.get("label") or f"STEP {index-1}")
        projection.cell(index, 2, step_count)
        projection.cell(index, 3, "=\'PLAN INPUTS\'!$B$3" if index == 2 else f"=E{index-1}")
        projection.cell(index, 6, base_rate)
        projection.cell(index, 4, f"=C{index}*((1+F{index}/100)^B{index}-1)")
        projection.cell(index, 5, f"=C{index}+D{index}")
        projection.cell(index, 7, "YES" if item.get("target_hit") else "NO")
    _style_sheet(projection, 1)
    for col, width in enumerate([20, 16, 22, 18, 22, 20, 14], 1):
        projection.column_dimensions[projection.cell(1, col).column_letter].width = width
    for row in projection.iter_rows(min_row=2, max_row=1 + len(plan.get("table") or [])):
        for cell in row:
            if cell.column in (3, 4, 5):
                cell.number_format = '#,##0.00;[Red]-#,##0.00'
            elif cell.column == 6:
                cell.number_format = '0.0000"%"'
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import PatternFill
    projection.conditional_formatting.add(
        f"G2:G{max(2, 1 + len(plan.get('table') or []))}",
        CellIsRule(operator="equal", formula=['"YES"'],
                   fill=PatternFill("solid", fgColor="C6EFCE")))
    projection.conditional_formatting.add(
        f"G2:G{max(2, 1 + len(plan.get('table') or []))}",
        CellIsRule(operator="equal", formula=['"NO"'],
                   fill=PatternFill("solid", fgColor="FCE4D6")))

    daily = wb.create_sheet("DAILY TARGET")
    daily.merge_cells("A1:F1")
    daily["A1"] = "TODAY'S DAILY TARGET — LIVE STATUS AT EXPORT"
    daily["A1"].font = Font(name="Aptos Display", size=17, bold=True, color="E3B341")
    status_text = "TARGET ACHIEVED" if target_achieved else ("TARGET NOT SET" if not target_goal else "IN PROGRESS")
    daily.merge_cells("A3:F3")
    daily["A3"] = f"{status_text}  ·  {target_pct or 0:.1f}%"
    daily["A3"].font = Font(name="Aptos Display", size=20, bold=True,
                            color="FFFFFF" if target_achieved else "253247")
    daily["A3"].fill = PatternFill("solid", fgColor="2E7D32" if target_achieved else "B7791F")
    daily["A3"].alignment = Alignment(horizontal="center", vertical="center")
    daily.row_dimensions[3].height = 36
    daily.append(["METRIC", "VALUE"])
    for item in [("Realized today (USD)", target_actual), ("Daily target (USD)", target_goal),
                 ("Completion (%)", target_pct), ("Remaining (USD)", target_remaining),
                 ("Target achieved", "YES" if target_achieved else "NO")]:
        daily.append(list(item))
    _style_sheet(daily, 4)
    daily.column_dimensions["A"].width = 34
    daily.column_dimensions["B"].width = 24
    daily["A3"].fill = PatternFill("solid", fgColor="2E7D32" if target_achieved else
                                   ("596579" if not target_goal else "B7791F"))
    for cell in (daily["A5"], daily["B5"]):
        cell.number_format = '#,##0.00;[Red]-#,##0.00'
    for cell in (daily["A6"], daily["B6"]):
        cell.number_format = '#,##0.00;[Red]-#,##0.00'
    return wb


def export_plan_xlsx(path, plan, logo_path="", provider_name="Signal Provider"):
    try:
        from openpyxl import Workbook
    except Exception as exc:
        raise RuntimeError("openpyxl is required for the branded plan workbook.") from exc
    jpeg, px, png = _logo_assets(logo_path)
    wb = Workbook()
    wb.properties.creator = str(provider_name or "Signal Provider")
    wb.properties.title = f"{provider_name} Editable Trading Plan"
    summary = wb.active
    summary.title = "OVERVIEW"
    summary.merge_cells("A1:H1")
    summary["A1"] = f"{provider_name} — TRADING PLAN"
    from openpyxl.styles import Alignment, Font, PatternFill
    summary["A1"].font = Font(name="Aptos Display", size=20, bold=True, color="E3B341")
    stream = _excel_logo(summary, png, "J1") if png else None
    summary_rows = [
        ("Starting capital USD", plan.get("capital")),
        ("Risk per trade USD", plan.get("risk_usd")),
        ("Daily expected USD", plan.get("per_day")),
        ("Monthly expected USD", plan.get("per_month")),
        ("Expected return R / trade", plan.get("expectancy_r")),
        ("Win rate used %", plan.get("win")),
        ("Reward : risk", plan.get("rr")),
        ("Trading cadence", plan.get("per")),
    ]
    summary.append(["METRIC", "VALUE"])
    for item in summary_rows:
        summary.append(list(item))
    _style_sheet(summary, 2)
    summary.column_dimensions["A"].width = 34
    summary.column_dimensions["B"].width = 21
    state = plan.get("daily_target_status") if isinstance(plan.get("daily_target_status"), dict) else {}
    actual = _num(state.get("net"))
    goal = _num(state.get("target"))
    pct = _num(state.get("done_pct")) or 0.0
    achieved = bool(state.get("achieved"))
    banner_row = 12
    summary.merge_cells(start_row=banner_row, start_column=1, end_row=banner_row, end_column=8)
    summary.cell(banner_row, 1, ("DAILY TARGET ACHIEVED" if achieved else
                                 ("DAILY TARGET NOT SET" if not goal else "DAILY TARGET IN PROGRESS"))
                 + f"  ·  {pct:.1f}%  ·  Actual {actual or 0:+,.2f} USD / Target {goal or 0:,.2f} USD")
    summary.cell(banner_row, 1).font = Font(name="Aptos Display", size=14, bold=True,
                                           color="FFFFFF")
    summary.cell(banner_row, 1).fill = PatternFill("solid", fgColor="2E7D32" if achieved else
                                                   ("596579" if not goal else "B7791F"))
    summary.cell(banner_row, 1).alignment = Alignment(horizontal="center", vertical="center")
    summary.row_dimensions[banner_row].height = 30
    _add_plan_sheets(wb, plan, png, logo_streams=[])
    _set_software_footer(wb)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(path))
    _ = stream
    return path


def _pdf_table(pdf, y, rows, headers, widths, colors=None, row_h=17.0, min_y=66.0,
               color_col=None):
    """Small custom table for Provider PDFs; avoids shared global column state."""
    x0, total = 34.0, 527.0
    if sum(widths) > total:
        scale = total / sum(widths)
        widths = [w * scale for w in widths]
    pdf.rect(x0, y - 16, total, 16, pdf.T("head"))
    x = x0
    for head, width in zip(headers, widths):
        pdf.text(x + 4, y - 11, str(head)[:16], 2, 6.4, pdf.T("white"))
        x += width
    y -= 20
    for index, row in enumerate(rows):
        if y < min_y:
            pdf.new_page()
            y = pdf.small_header() - 20
            pdf.rect(x0, y - 16, total, 16, pdf.T("head"))
            x = x0
            for head, width in zip(headers, widths):
                pdf.text(x + 4, y - 11, str(head)[:16], 2, 6.4, pdf.T("white"))
                x += width
            y -= 20
        if index % 2:
            pdf.rect(x0, y - 13, total, 15, pdf.T("zebra"))
        x = x0
        for col, (value, width) in enumerate(zip(row, widths)):
            text = str(value if value is not None else "-")
            max_chars = max(4, int(width / 3.6))
            if len(text) > max_chars:
                text = text[:max_chars - 1] + "~"
            color = pdf.T("text")
            color_index = (len(row) - 1) if color_col is None else int(color_col)
            if colors and index < len(colors) and colors[index] is not None and col == color_index:
                color = colors[index]
            pdf.text(x + 4, y - 8, text, 1, 6.2, color)
            x += width
        y -= row_h
    return y - 8


def export_provider_pdf(path, publications, trades=None, engine=None, logo_path="",
                        provider_name="Signal Provider", plan=None,
                        destination_id=None, destination_name=""):
    """Create a polished, multi-page PDF with the uploaded provider logo."""
    if engine is None or not hasattr(engine, "PremiumPDF"):
        raise RuntimeError("The premium PDF engine is unavailable.")
    if destination_id is not None:
        publications, trades = _filter_publications_for_destination(
            publications, trades, destination_id, destination_name)
        provider_name = str(destination_name or provider_name or "Signal Provider")
    data = provider_performance(publications, trades, engine)
    periods, rows = data["periods"], data["rows"]
    jpeg, px, _png = _logo_assets(logo_path)
    pdf = engine.PremiumPDF(jpeg, px, dark=True, by=provider_name,
                            title="PROVIDER PERFORMANCE", subtitle=datetime.now().strftime("%B %Y"),
                            brand_name=provider_name)
    today = periods["today"]
    pdf.cover([("today's signals", str(today["signals"])),
               ("today's win rate", "Not decided" if today["win_rate"] is None else f"{today['win_rate']:.1f}%"),
               ("today's actual MT5 pips W/L", _pips_wl_label(today, "actual")),
               ("today's estimated signal pips W/L", _pips_wl_label(today, "nominal")),
               ("today's actual net USD", "Not recorded" if today["actual_net"] is None else f"{today['actual_net']:+,.2f}"),
               ("best signal", (today["best_signal"]["symbol"] if today.get("best_signal") else "Not recorded"))],
              badge="PROVIDER PERFORMANCE  •  SIGNAL STUDIO")
    pdf.new_page()
    y = pdf.header("PROVIDER PERFORMANCE", right="SIGNAL STUDIO")
    month = periods["month"]
    y = pdf.kpis(y, [("SIGNALS THIS MONTH", str(month["signals"]), pdf.T("gold")),
                     ("WIN RATE", "-" if month["win_rate"] is None else f"{month['win_rate']:.1f}%", pdf.T("green")),
                     ("ACTUAL PIPS W/L", _pips_wl_label(month, "actual"), pdf.T("text")),
                     ("ACTUAL NET USD", "-" if month["actual_net"] is None else f"{month['actual_net']:+,.2f}", pdf.T("green" if (month["actual_net"] or 0) >= 0 else "red"))])
    y = pdf.section(y, "DAILY / WEEKLY / MONTHLY / ALL TIME", "signal counts + linked outcomes")
    summary_rows = []
    summary_colors = []
    for key in ("today", "week", "month", "all"):
        item = periods[key]
        summary_rows.append([item["label"], item["signals"], item["wins"], item["losses"], item["be"],
                             "-" if item["win_rate"] is None else f"{item['win_rate']:.1f}%",
                             sum(item["tp_levels"].values()),
                             _pips_wl_label(item, "actual"),
                             "-" if item["actual_net"] is None else f"{item['actual_net']:+.2f}",
                             _pips_wl_label(item, "nominal")])
        summary_colors.append(pdf.T("green") if (item["actual_net"] or 0) >= 0 else pdf.T("red"))
    y = _pdf_table(pdf, y, summary_rows,
                   ["PERIOD", "SIGNALS", "WINS", "SL", "BE", "WIN%", "TP HITS", "MT5 W/L PIPS", "NET USD", "SIG W/L PIPS"],
                   [70, 42, 34, 32, 32, 45, 42, 78, 66, 78], summary_colors, row_h=20)
    y = pdf.section(y, "TOP SIGNAL", "highest recorded actual USD, otherwise nominal signal pips")
    best = month.get("best_signal") or periods["all"].get("best_signal")
    if best:
        basis = month.get("best_basis") if month.get("best_signal") else periods["all"].get("best_basis")
        best_metric = (f"{best.get('actual_net'):+,.2f} USD" if best.get("actual_net") is not None
                       else f"{best.get('nominal_pips'):+,.1f} nominal pips")
        pdf.text(40, y, f"{best.get('symbol', '')} {best.get('direction', '')}  |  "
                        f"{best_metric}  |  {best.get('status', '')}  |  {basis}", 1, 8, pdf.T("gold"))
        y -= 20
    else:
        pdf.text(40, y, "No completed or recorded outcomes for this period.", 1, 8, pdf.T("muted"))
        y -= 18
    actual_bars = [(periods[key]["label"], periods[key]["actual_net"])
                   for key in ("today", "week", "month") if periods[key]["actual_net"] is not None]
    if actual_bars:
        y = pdf.bars(y - 4, actual_bars, title="RECORDED NET P&L", note="linked MT5 journal only",
                     h=max(60.0, min(100.0, len(actual_bars) * 25.0)), unit="USD")
    pdf.text(40, 54, "Actual MT5 pips/USD require linked closed journal trades. Nominal signal pips are not broker P&L.",
             1, 6.3, pdf.T("muted"))
    pdf.footer()

    destination_rows = []
    for item in data.get("groups") or []:
        destination_rows.append([item.get("destination", "-"), item.get("signals", 0),
                                item.get("actual_trades", 0), item.get("market", 0),
                                item.get("limit", 0), item.get("wins", 0),
                                item.get("losses", 0), item.get("be", 0),
                                item.get("tp_hits", 0), item.get("sl_hits", 0)])
    if not destination_rows:
        destination_rows = [["No destinations recorded", 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    destination_per_page = 26
    for offset in range(0, len(destination_rows), destination_per_page):
        pdf.new_page()
        y = pdf.header("DESTINATION PERFORMANCE", right=f"{offset + 1}-{min(offset + destination_per_page, len(destination_rows))} OF {len(destination_rows)}")
        y = pdf.section(y, "DESTINATIONS USED", "publication counts + linked closed MT5 trades")
        page_rows = destination_rows[offset:offset + destination_per_page]
        y = _pdf_table(pdf, y, page_rows,
                       ["DESTINATION", "SIGNALS", "MT5", "MARKET", "LIMIT", "WINS", "SL", "BE", "TP HITS", "SL HITS"],
                       [140, 48, 45, 42, 42, 40, 36, 36, 48, 48], row_h=18)
        pdf.text(40, 46, "Signal counts are per destination publication; MT5 counts include linked closed journal trades only.",
                 1, 6.1, pdf.T("muted"))
        pdf.footer()

    detail_rows = []
    row_colors = []
    for item in rows:
        detail_rows.append([item["created"], f"{item['symbol']} {item['direction']}", item["status"],
                            ",".join(f"{x}" for x in item["tp_hits"]) or "-",
                            "-" if item["nominal_pips"] is None else f"{item['nominal_pips']:+.1f}",
                            "-" if item["actual_pips"] is None else f"{item['actual_pips']:+.1f}",
                            "-" if item["actual_net"] is None else f"{item['actual_net']:+.2f}",
                            str(item["targets"])])
        net = item["actual_net"]
        row_colors.append(pdf.T("green") if net is not None and net > 0 else
                          (pdf.T("red") if net is not None and net < 0 else None))
    per_page = 31
    if not detail_rows:
        detail_rows = [["-", "No provider signals", "-", "-", "-", "-", "-", "0"]]
        row_colors = [None]
    for offset in range(0, len(detail_rows), per_page):
        pdf.new_page()
        y = pdf.header("PUBLISHED SIGNAL DETAIL", right=f"{offset + 1}-{min(offset + per_page, len(detail_rows))} OF {len(detail_rows)}")
        y = pdf.section(y, "SIGNAL JOURNAL", "one row per published signal")
        y = _pdf_table(pdf, y, detail_rows[offset:offset + per_page],
                       ["CREATED", "SYMBOL / DIR", "STATUS", "TP HIT", "SIG PIPS", "MT5 PIPS", "NET USD", "DEST"],
                       [72, 115, 78, 42, 58, 58, 67, 37], row_colors[offset:offset + per_page],
                       row_h=19, color_col=6)
        pdf.text(40, 46, "Signal pips are price-distance estimates; actual MT5 results are linked journal records only.",
                 1, 6.3, pdf.T("muted"))
        pdf.footer()
    _pdf_linked_trade_journal(pdf, rows, trades, engine)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.save(path)
    return path


def export_provider_daily_pdf(path, publications, trades=None, engine=None, logo_path="",
                              destination_id=None, destination_name="", now=None):
    """Create a destination-branded PDF containing only today's sent signals for one chat."""
    if engine is None or not hasattr(engine, "PremiumPDF"):
        raise RuntimeError("The premium PDF engine is unavailable.")
    now = now if isinstance(now, datetime) else (datetime.fromtimestamp(float(now)).astimezone()
                                                   if now is not None else datetime.now().astimezone())
    if now.tzinfo is None:
        now = now.astimezone()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    end = now.timestamp()
    name = str(destination_name or destination_id or "Telegram destination").strip()
    daily_publications, daily_trades = _filter_publications_for_destination(
        publications, trades, destination_id, name, start_ts=start, end_ts=end,
        require_message_id=True)
    if not daily_publications:
        raise RuntimeError(f"No successfully sent Provider signals for {name} on {now:%Y-%m-%d}.")
    data = provider_performance(daily_publications, daily_trades, engine, now=now)
    stats = data["periods"]["today"]
    rows = [row for row in data["rows"]
            if start <= float(row.get("created_ts") or 0.0) <= end]
    jpeg, px, _png = _logo_assets(logo_path)
    pdf = engine.PremiumPDF(jpeg, px, dark=True, by=name,
                            title="DAILY SIGNAL REPORT", subtitle=now.strftime("%Y-%m-%d"),
                            brand_name=name)
    pdf.cover([
        ("signals sent today", str(stats["signals"])),
        ("wins / losses / break-even", f"{stats['wins']} / {stats['losses']} / {stats['be']}"),
        ("win rate", "-" if stats["win_rate"] is None else f"{stats['win_rate']:.1f}%"),
        ("linked MT5 net USD", "Not recorded" if stats["actual_net"] is None else f"{stats['actual_net']:+,.2f}"),
        ("actual MT5 pips W/L", _pips_wl_label(stats, "actual")),
        ("estimated signal pips W/L", _pips_wl_label(stats, "nominal")),
    ], badge=f"DAILY PROVIDER REPORT  -  {now:%Y-%m-%d}")
    pdf.new_page()
    y = pdf.header("DAILY PERFORMANCE", right=name[:40], date=now.strftime("%d %b %Y"))
    y = pdf.kpis(y, [
        ("SIGNALS", str(stats["signals"]), pdf.T("gold")),
        ("WIN RATE", "-" if stats["win_rate"] is None else f"{stats['win_rate']:.1f}%", pdf.T("green")),
        ("ACTUAL NET USD", "-" if stats["actual_net"] is None else f"{stats['actual_net']:+,.2f}",
         pdf.T("green" if (stats["actual_net"] or 0) >= 0 else "red")),
        ("LINKED MT5 TRADES", str(stats["actual_trades"]), pdf.T("text")),
    ])
    y = pdf.section(y, "DESTINATION SUMMARY", "today's successfully published signals only")
    y = _pdf_table(pdf, y, [[
        stats["signals"], stats["wins"], stats["losses"], stats["be"],
        "-" if stats["win_rate"] is None else f"{stats['win_rate']:.1f}%",
        sum(stats["tp_levels"].values()), stats["actual_trades"],
        _pips_wl_label(stats, "actual"),
        "-" if stats["actual_net"] is None else f"{stats['actual_net']:+.2f}",
        _pips_wl_label(stats, "nominal")]],
        ["SIGNALS", "WINS", "SL", "BE", "WIN%", "TP HITS", "MT5 TRADES", "ACTUAL PIPS W/L", "NET USD", "EST. PIPS W/L"],
        [43, 35, 30, 30, 44, 47, 55, 88, 70, 85], row_h=22)
    pdf.text(40, max(82, y - 4),
             "Actual P&L/pips use linked closed MT5 journal trades only; signal-distance estimates are not broker P&L.",
             1, 6.1, pdf.T("muted"))
    pdf.footer()
    detail_rows = []
    row_colors = []
    for row in rows:
        created = row.get("created") or "-"
        detail_rows.append([
            created, f"{row.get('symbol', '')} {row.get('direction', '')}",
            str(row.get("order_type") or "LIMIT"), str(row.get("entry") or "-"),
            str(row.get("sl") or "-"), str(row.get("tps") or "-"),
            str(row.get("status") or "-"), str(row.get("outcome") or "PENDING"),
            ",".join(str(x) for x in (row.get("tp_hits") or [])) or "-",
            "-" if row.get("actual_pips") is None else f"{row['actual_pips']:+.1f}",
            "-" if row.get("actual_net") is None else f"{row['actual_net']:+.2f}",
            "-" if row.get("nominal_pips") is None else f"{row['nominal_pips']:+.1f}",
        ])
        net = row.get("actual_net")
        row_colors.append(pdf.T("green") if net is not None and net > 0 else
                          (pdf.T("red") if net is not None and net < 0 else None))
    per_page = 27
    for offset in range(0, len(detail_rows), per_page):
        pdf.new_page()
        y = pdf.header("SIGNAL DETAIL", right=f"{offset + 1}-{min(offset + per_page, len(detail_rows))} / {len(detail_rows)}",
                       date=now.strftime("%d %b %Y"))
        y = pdf.section(y, "SIGNALS SENT TO THIS DESTINATION", name[:60])
        y = _pdf_table(pdf, y, detail_rows[offset:offset + per_page],
            ["TIME", "SYMBOL/DIR", "TYPE", "ENTRY", "SL", "TPs", "STATUS", "OUTCOME", "TP HIT", "ACT PIPS", "NET USD", "EST PIPS"],
            [47, 76, 39, 41, 38, 54, 55, 48, 42, 50, 51, 48],
            row_colors[offset:offset + per_page], row_h=20, color_col=10)
        pdf.text(40, 46, "Only signals successfully sent to this destination today are included. "
                 "EdgeQuant Sentinel reports software credit; this is not financial advice.",
                 1, 6.0, pdf.T("muted"))
        pdf.footer()
    _pdf_linked_trade_journal(pdf, rows, daily_trades, engine)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.save(path)
    return path


def export_plan_pdf(path, plan, logo_path="", provider_name="Signal Provider", engine=None):
    if engine is None or not hasattr(engine, "PremiumPDF"):
        raise RuntimeError("The premium PDF engine is unavailable.")
    jpeg, px, _png = _logo_assets(logo_path)
    pdf = engine.PremiumPDF(jpeg, px, dark=True, by=provider_name,
                            title="EDITABLE TRADING PLAN", subtitle=str(plan.get("per") or "DAYS"),
                            brand_name=provider_name)
    cadence = str(plan.get("per") or "DAYS").upper()
    label = "trading days" if cadence == "DAYS" else "months"
    count = plan.get("days") if cadence == "DAYS" else plan.get("months")
    target_state = plan.get("daily_target_status") if isinstance(plan.get("daily_target_status"), dict) else {}
    _daily_target_label = "ACHIEVED" if target_state.get("achieved") else (
        "NOT SET" if not _num(target_state.get("target")) else "IN PROGRESS")
    pdf.cover([("starting capital", f"{float(plan.get('capital') or 0):,.2f} USD"),
               ("risk per trade", f"{float(plan.get('risk_usd') or 0):,.2f} USD  ({float(plan.get('risk_pct') or 0):g}%)"),
               ("daily target status", f"{_daily_target_label}  ·  {_num(target_state.get('done_pct')) or 0:.1f}%"),
               ("today realized / target", f"{_num(target_state.get('net')) or 0:+,.2f} / {_num(target_state.get('target')) or 0:,.2f} USD"),
               ("daily expected target", f"{float(plan.get('per_day') or 0):+,.2f} USD"),
               ("win rate / reward-risk", f"{float(plan.get('win') or 0):.1f}%  /  {float(plan.get('rr') or 0):.2f}:1"),
               ("plan horizon", f"{count} {label}"),
               ("expectancy", f"{float(plan.get('expectancy_r') or 0):+.3f} R per trade")],
              badge="EDITABLE TRADING PLAN")
    pdf.new_page()
    y = pdf.header("TRADING PLAN", right="PROJECTION")
    y = pdf.kpis(y, [("CAPITAL", f"{float(plan.get('capital') or 0):,.2f} USD", pdf.T("gold")),
                     ("RISK / TRADE", f"{float(plan.get('risk_usd') or 0):,.2f} USD", pdf.T("amber")),
                     ("EXPECTED / DAY", f"{float(plan.get('per_day') or 0):+,.2f} USD", pdf.T("green")),
                     ("EXPECTED / MONTH", f"{float(plan.get('per_month') or 0):+,.2f} USD", pdf.T("green"))])
    target_state = plan.get("daily_target_status") if isinstance(plan.get("daily_target_status"), dict) else {}
    target_goal = _num(target_state.get("target"))
    target_actual = _num(target_state.get("net"))
    target_pct = _num(target_state.get("done_pct")) or 0.0
    target_achieved = bool(target_state.get("achieved"))
    target_label = "TARGET ACHIEVED" if target_achieved else ("TARGET NOT SET" if not target_goal else "IN PROGRESS")
    target_color = pdf.T("green") if target_achieved else (pdf.T("muted") if not target_goal else pdf.T("amber"))
    y = pdf.section(y, "TODAY'S DAILY TARGET", "live status captured at export")
    y = pdf.kpis(y, [(target_label, f"{target_pct:.1f}%", target_color),
                     ("REALIZED TODAY", f"{target_actual or 0:+,.2f} USD", pdf.T("green" if (target_actual or 0) >= 0 else "red")),
                     ("DAILY TARGET", f"{target_goal or 0:,.2f} USD", pdf.T("gold")),
                     ("REMAINING", f"{_num(target_state.get('remaining')) or 0:,.2f} USD", pdf.T("amber"))])
    y = pdf.section(y, "RISK AND EXPECTANCY INPUTS", "editable in the Excel companion")
    rows = [["Risk % / trade", f"{float(plan.get('risk_pct') or 0):g}%", "Win rate used", f"{float(plan.get('win') or 0):.1f}%"],
            ["Reward : risk", f"{float(plan.get('rr') or 0):.2f}:1", "Expectancy", f"{float(plan.get('expectancy_r') or 0):+.3f} R"],
            ["Daily stop guide", f"{float(plan.get('day_stop') or 0):,.2f} USD", "Weekly stop guide", f"{float(plan.get('week_stop') or 0):,.2f} USD"],
            ["Signals per day", str(plan.get("trades_day") or "-"), "Plan cadence", cadence]]
    y = _pdf_table(pdf, y, rows, ["INPUT", "VALUE", "INPUT", "VALUE"], [140, 120, 140, 127], row_h=20)
    y = pdf.section(y, "COMPOUNDING PROJECTION", f"{count} {label}; illustrative, not guaranteed")
    projection = []
    for item in plan.get("table") or []:
        projection.append([item.get("label") or "-", item.get("start"), item.get("gain"),
                           item.get("end"), f"{float(item.get('pct') or 0):+.3f}%",
                           "YES" if item.get("target_hit") else "NO"])
    if not projection:
        projection = [["-", "-", "-", "-", "-", "-"]]
    y = _pdf_table(pdf, y, projection[:32], ["STEP", "START USD", "GAIN USD", "END USD", "RATE", "TARGET"],
                   [70, 92, 92, 92, 92, 89], row_h=16)
    for offset in range(32, len(projection), 32):
        pdf.new_page()
        y = pdf.header("TRADING PLAN", right="PROJECTION CONTINUED")
        y = _pdf_table(pdf, y, projection[offset:offset + 32],
                       ["STEP", "START USD", "GAIN USD", "END USD", "RATE", "TARGET"],
                       [70, 92, 92, 92, 92, 89], row_h=16)
        pdf.footer()
    pdf.text(40, 50, "Illustrative projection only. It is not financial advice and does not guarantee results.",
             1, 7, pdf.T("muted"))
    pdf.footer()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.save(path)
    return path

