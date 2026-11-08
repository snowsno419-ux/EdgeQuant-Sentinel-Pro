"""Cross-post, account-scoped order-intent duplicate protection.

For entry-bearing direct LIMIT signals, identify a *pair* by canonical symbol,
side, source entry, shared stop and Layer-2 signal TP. Layer-1's configurable
quick target does not change the identity of the original signal.

A durable exclusive-create receipt precedes ANY broker order_send. This means
reconnects, simultaneous Telegram sources and independent MT5 workers cannot
blindly submit the same pair twice. An interrupted or ambiguous submission is
fail-closed; clearing receipts requires checking MT5 orders/history first.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import time


_ALIASES = {"GOLD": "XAUUSD", "XAU": "XAUUSD", "SILVER": "XAGUSD", "XAG": "XAGUSD"}
_COMMON_SYMBOLS = (
    "XAUUSD", "XAGUSD", "XPTUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "NZDUSD", "USDCAD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY",
    "EURAUD", "EURCHF", "CADJPY", "CHFJPY", "NZDJPY", "GBPCHF", "GBPAUD",
    "GBPCAD", "GBPNZD", "AUDCAD", "AUDCHF", "AUDNZD", "EURNZD", "EURCAD",
    "CADCHF", "NZDCAD", "NZDCHF", "USDTRY", "USDZAR", "USDMXN", "US30",
    "US100", "US500", "GER40", "UK100", "JP225", "USOIL", "UKOIL",
    "BTCUSD", "ETHUSD",
)


def _symbol(raw):
    s = str(raw or "").strip().upper().replace("/", "")
    if s in _ALIASES:
        return _ALIASES[s]
    for canonical in sorted(_COMMON_SYMBOLS, key=len, reverse=True):
        if s == canonical or (s.startswith(canonical) and len(s) > len(canonical) and
                              (s[len(canonical)] in ".-_" or s[len(canonical):] in ("M", "MICRO", "PRO", "RAW"))):
            return canonical
    return s


def _price(value):
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d <= 0:
            raise ValueError("price must be positive")
        return str(d.quantize(Decimal("0.00000001")).normalize())
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError("invalid price") from e


def _order_groups(plan):
    groups = defaultdict(list)
    for row in plan:
        if not isinstance(row, dict) or not row.get("direct_limit"):
            raise ValueError("duplicate guard requires direct LIMIT orders")
        groups[_price(row.get("src_price"))].append(row)
    for source_entry, rows in groups.items():
        if len(rows) % 2:
            raise ValueError("expected paired layers per entry")
        # A single Telegram message can itself contain a repeated level.
        # Treat subsequent two-layer pairs as duplicates, not extra entries.
        for offset in range(0, len(rows), 2):
            pair = rows[offset:offset + 2]
            if sorted(int(x.get("layer") or 0) for x in pair) != [1, 2]:
                raise ValueError("expected exactly Layer 1 and Layer 2")
            if _price(pair[0].get("sl")) != _price(pair[1].get("sl")):
                raise ValueError("layer stop-loss mismatch")
            if _price(pair[0].get("price")) != _price(pair[1].get("price")):
                raise ValueError("layer entry mismatch")
            yield source_entry, pair


def identity_key(*, login, server, symbol, direction, entry, sl, target):
    """Same signal means same account, symbol, side, original entry, SL, L2 TP."""
    account = int(login or 0)
    host = str(server or "").strip().casefold()
    side = str(direction or "").strip().upper()
    sym = _symbol(symbol)
    if account <= 0 or not host or side not in ("BUY", "SELL") or not sym:
        raise ValueError("unverified MT5 account/symbol/side")
    contents = [account, host, sym, side, _price(entry), _price(sl), _price(target)]
    return hashlib.sha256(json.dumps(contents, separators=(",", ":")).encode("utf-8")).hexdigest()


def _default_folder():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if os.name == "nt" and base:
        return Path(base) / "EdgeQuant" / "duplicate_signal_claims_v1"
    return Path(__file__).resolve().parent / "duplicate_signal_claims_v1"


def _active_broker_duplicate(mt5_api, symbol, rows, magic):
    """Also recognize active pending orders from *before* this feature was added.

    Do not compare to the market quote; only inspect existing own MT5 tickets.
    If the connector cannot read current orders/positions, fail closed.
    """
    if mt5_api is None:
        return False
    entry = float(rows[0]["price"])
    sl = float(rows[0]["sl"])
    tps = [float(row["tp"]) for row in rows]
    # Only orders/positions owned by EdgeQuant. Avoid blocking unrelated orders.
    for collection in ("orders_get", "positions_get"):
        method = getattr(mt5_api, collection, None)
        if method is None:
            raise RuntimeError(f"MT5 {collection} unavailable")
        found = method(symbol=symbol)
        if found is None:
            raise RuntimeError(f"MT5 {collection} unavailable / cannot verify existing orders")
        for item in found:
            if int(getattr(item, "magic", -1) or -1) != int(magic):
                continue
            price = float(getattr(item, "price_open", 0) or 0)
            item_sl = float(getattr(item, "sl", 0) or 0)
            item_tp = float(getattr(item, "tp", 0) or 0)
            if (abs(price - entry) < 0.00000001 and abs(item_sl - sl) < 0.00000001 and
                    any(abs(item_tp - tp) < 0.00000001 for tp in tps)):
                return True
    return False


def claim_plan(plan, *, login, server, broker, symbol, direction, mt5_api=None,
               magic=None, folder=None, dry_run=False):
    """Return (eligible_plan, duplicate_count, claims, error).

    Duplicate rows stay in `plan` as status=duplicate for audit/journal, but are
    excluded from `eligible_plan` before execute_plan is called.
    """
    claims = []
    dup_count = 0
    eligible = []
    try:
        groups = list(_order_groups(plan))
        root = Path(folder) if folder is not None else _default_folder()
        if not dry_run:
            root.mkdir(parents=True, exist_ok=True)
        for src, rows in groups:
            target_row = next(x for x in rows if int(x["layer"]) == 2)
            key = identity_key(login=login, server=server, symbol=symbol,
                               direction=direction, entry=src,
                               sl=rows[0]["sl"], target=target_row["tp"])
            receipt = root / (key + ".json")
            duplicate = receipt.exists()
            if not duplicate and mt5_api is not None:
                duplicate = _active_broker_duplicate(mt5_api, symbol, rows, magic)
            if not duplicate and not dry_run:
                record = {"version": 1, "created_ts": time.time(),
                          "symbol": _symbol(symbol), "direction": str(direction).upper(),
                          "entry": src, "sl": _price(rows[0]["sl"]),
                          "layer2_tp": _price(target_row["tp"]), "broker": str(broker),
                          "state": "claimed_before_submission", "tickets": []}
                try:
                    with receipt.open("x", encoding="utf-8") as fh:
                        json.dump(record, fh, ensure_ascii=False)
                        fh.flush()
                        os.fsync(fh.fileno())
                except FileExistsError:
                    duplicate = True  # another process got the atomic claim
                else:
                    claims.append((receipt, rows))
            if duplicate:
                dup_count += 1
                for row in rows:
                    row["kind"] = "DUPLICATE"
                    row["status"] = "duplicate"
                    row["error"] = "identical account/symbol/side/entry/SL/TP already submitted or active"
            else:
                eligible.extend(rows)
        return eligible, dup_count, claims, ""
    except Exception as exc:
        # Never trade any partly claimed plan on a broken guard. All claims
        # already created remain as crash-safe fences until owner reconciliation.
        return [], dup_count, claims, "duplicate guard failed closed: " + str(exc)[:180]


def finalize_claims(claims):
    """Annotate receipts after submission; a crash retains the initial fence."""
    for path, rows in claims:
        try:
            accepted = [int(r["ticket"]) for r in rows
                        if str(r.get("status") or "").lower() in ("pending", "open")
                        and int(r.get("ticket") or 0) > 0]
            states = [str(r.get("status") or "").lower() for r in rows]
            state = ("placed" if accepted else "uncertain" if any(
                x in ("uncertain", "partial", "not_attempted") for x in states)
                     else "rejected_or_not_sent")
            record = json.loads(path.read_text(encoding="utf-8"))
            record.update(state=state, tickets=accepted, updated_ts=time.time())
            tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
            with tmp.open("x", encoding="utf-8") as fh:
                json.dump(record, fh, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except Exception:
            # Preserve original claim; it still prevents an unsafe duplicate.
            pass
