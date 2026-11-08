#!/usr/bin/env python3
"""EdgeQuant Web Phase 1 — read-only local Windows agent.

Serves a same-origin web dashboard and reads the existing EdgeQuant journal,
source configuration, and engine heartbeat. No cloud connection, credentials,
MT5 actions, or Telegram actions are exposed in this phase.
"""
from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

APP_HOME = Path(os.environ.get("EDGEQUANT_HOME", Path(__file__).resolve().parent)).expanduser().resolve()
WEB_DIR = Path(__file__).resolve().parent / "edgequant_web"
INDEX_FILE = WEB_DIR / "index.html"
ENGINE_FILE = APP_HOME / "edgequant_auto.py"
STATUS_FILE = APP_HOME / "edgequant_status.json"
JOURNAL_FILE = APP_HOME / "edgequant_trades.jsonl"
CHANNEL_MONITOR_FILE = APP_HOME / "edgequant_channel_monitor.json"
SIGNAL_AUDIT_FILE = APP_HOME / "edgequant_signal_audit.jsonl"
SIGNAL_REVIEW_FILE = APP_HOME / "edgequant_signal_review.jsonl"
SIGNAL_DEFERRED_FILE = APP_HOME / "edgequant_signal_deferred.json"
VERSION = "1.9.12"
WEB_BUILD = "Web Phase 2 • Signal Monitor • local read-only"
STATUS_FRESH_SECONDS = 180

SAFE_TRADE_FIELDS = (
    "id", "source", "source_type", "symbol", "direction", "kind", "order_type",
    "entry", "price", "sig_entry", "open_price", "close_price", "sl", "tp", "lot",
    "pip", "status", "result", "net", "pips", "placed_ts", "opened_ts", "closed_ts",
    "ticket", "tag", "broker",
)


def _json_literal_assignments(source: str) -> dict:
    """Read literal top-level settings without executing edgequant_auto.py."""
    wanted = {
        "VERSION", "BOT_NAME", "LIMIT_CHANNELS", "MARKET_CHANNELS", "CHANNEL_IDS",
        "CHANNEL_ID_NAMES", "TRADE_LOG", "STATUS_FILE", "TG_STATUS_FRESH_S",
    }
    found = {}
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return found
    for node in tree.body:
        targets = []
        value_node = None
        if isinstance(node, ast.Assign):
            targets, value_node = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value_node = [node.target], node.value
        if value_node is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    found[target.id] = ast.literal_eval(value_node)
                except Exception:
                    pass
    return found


def _engine_literals() -> dict:
    try:
        return _json_literal_assignments(ENGINE_FILE.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {}


def _status_snapshot() -> dict:
    try:
        data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        age = max(0.0, time.time() - float(data.get("ts") or 0))
        try:
            fresh_limit = float(_engine_literals().get("TG_STATUS_FRESH_S") or STATUS_FRESH_SECONDS)
        except (TypeError, ValueError):
            fresh_limit = STATUS_FRESH_SECONDS
        data["age_s"] = round(age, 1)
        data["fresh"] = age <= fresh_limit
        # Never pass through unexpected values or local file paths.
        mt5 = data.get("mt5") if isinstance(data.get("mt5"), dict) else {}
        data["mt5"] = {
            "login": mt5.get("login"),
            "balance": mt5.get("balance"),
            "currency": str(mt5.get("currency") or ""),
            "server": str(mt5.get("server") or ""),
        }
        data["telegram"] = bool(data.get("telegram")) if data["fresh"] else False
        return data
    except Exception:
        return {}


def _safe_float(value):
    try:
        value = float(value or 0)
        return value if math.isfinite(value) and value > 0 else None
    except (TypeError, ValueError):
        return None


def _safe_int(value, default=0):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return default


def _safe_signed_int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _tail_jsonl(path: Path, max_lines: int) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return list(__import__("collections").deque(fh, maxlen=max(1, int(max_lines))))
    except OSError:
        return []


def _read_channel_monitor() -> dict:
    try:
        data = json.loads(CHANNEL_MONITOR_FILE.read_text(encoding="utf-8"))
        rows = data.get("channels", {}) if isinstance(data, dict) else {}
        if not isinstance(rows, dict):
            return {"updated_ts": None, "channels": []}
        allowed = ("chat_id", "name", "category", "enabled", "connected", "cursor",
                   "last_event", "last_seen_ts", "last_seen_message_id",
                   "last_decision_ts", "last_decision_message_id", "last_outcome",
                   "last_reason", "last_history_check_ts", "last_history_status",
                   "last_history_reason", "retry_pending", "retry_message_id",
                   "retry_attempts", "retry_last_ts", "retry_after_ts",
                   "backlog_pending", "updated_ts")
        out = []
        for key, row in rows.items():
            if not isinstance(row, dict):
                continue
            cid = _safe_signed_int(row.get("chat_id", key))
            if not cid:
                continue
            item = {k: row[k] for k in allowed if k in row}
            item["chat_id"] = cid
            for k in ("name", "category", "last_event", "last_outcome", "last_reason",
                      "last_history_status", "last_history_reason"):
                if k in item:
                    item[k] = " ".join(str(item[k] or "").split())[:180]
            for k in ("cursor", "last_seen_message_id", "last_decision_message_id",
                      "retry_message_id", "retry_attempts"):
                if k in item:
                    item[k] = _safe_int(item[k])
            for k in ("last_seen_ts", "last_decision_ts", "last_history_check_ts",
                      "retry_last_ts", "retry_after_ts", "updated_ts"):
                if k in item:
                    item[k] = _safe_float(item[k])
            for k in ("enabled", "connected", "retry_pending", "backlog_pending"):
                if k in item:
                    item[k] = bool(item[k])
            out.append(item)
        out.sort(key=lambda x: str(x.get("name") or "").casefold())
        return {"updated_ts": _safe_float(data.get("updated_ts")), "channels": out[:100]}
    except Exception:
        return {"updated_ts": None, "channels": []}


def _read_signal_audit(limit: int = 100) -> list[dict]:
    limit = max(1, min(500, int(limit or 100)))
    rows = []
    for line in reversed(_tail_jsonl(SIGNAL_AUDIT_FILE, max(1000, limit * 10))):
        try:
            item = json.loads(line)
            if not isinstance(item, dict):
                continue
            rec = {"ts": _safe_float(item.get("ts")),
                   "event": str(item.get("event") or "")[:48],
                   "source": str(item.get("source") or "")[:120],
                   "chat_id": _safe_signed_int(item.get("chat_id")), 
                   "message_id": _safe_int(item.get("message_id")),
                   "category": str(item.get("category") or "")[:24],
                   "action": str(item.get("action") or "")[:40],
                   "confidence": str(item.get("confidence") or "")[:24],
                   "symbol": str(item.get("symbol") or "")[:32],
                   "direction": str(item.get("direction") or "")[:8],
                   "outcome": str(item.get("outcome") or "")[:48],
                   "reason": str(item.get("reason") or "")[:220],
                   "broker": str(item.get("broker") or "")[:80],
                   "tickets": [_safe_int(x) for x in (item.get("tickets") or [])[:20]],
                   "needs_review": bool(item.get("needs_review"))}
            rows.append(rec)
            if len(rows) >= limit:
                break
        except Exception:
            continue
    return rows


def _read_review_queue(limit: int = 100) -> list[dict]:
    limit = max(1, min(500, int(limit or 100)))
    rows = []
    for line in reversed(_tail_jsonl(SIGNAL_REVIEW_FILE, max(1000, limit * 10))):
        try:
            item = json.loads(line)
            if not isinstance(item, dict):
                continue
            rows.append({"ts": _safe_float(item.get("ts")),
                         "source": str(item.get("source") or "")[:120],
                         "chat_id": _safe_signed_int(item.get("chat_id")),
                         "message_id": _safe_int(item.get("message_id")),
                         "category": str(item.get("category") or "")[:24],
                         "message_ts": _safe_float(item.get("message_ts")),
                         "reason": str(item.get("reason") or "")[:220],
                         "kind": str(item.get("kind") or "unknown_signal")[:40],
                         "message_hash": str(item.get("message_hash") or "")[:24],
                         "text": str(item.get("text") or ""),
                         "status": str(item.get("status") or "needs_review")[:32]})
            if len(rows) >= limit:
                break
        except Exception:
            continue
    return rows


def _read_deferred_queue(limit: int = 100) -> list[dict]:
    limit = max(1, min(500, int(limit or 100)))
    try:
        data = json.loads(SIGNAL_DEFERRED_FILE.read_text(encoding="utf-8"))
        source = data.get("signals", []) if isinstance(data, dict) else []
        if not isinstance(source, list):
            return []
        source = [row for row in source if isinstance(row, dict)]
        source.sort(key=lambda row: _safe_float(row.get("created_ts")) or 0, reverse=True)
        return [{"id": str(row.get("id") or "")[:32],
                 "created_ts": _safe_float(row.get("created_ts")),
                 "updated_ts": _safe_float(row.get("updated_ts")),
                 "source": str(row.get("source") or "")[:120],
                 "chat_id": _safe_signed_int(row.get("chat_id")),
                 "message_id": _safe_int(row.get("message_id")),
                 "category": str(row.get("category") or "")[:24],
                 "message_ts": _safe_float(row.get("message_ts")),
                 "expires_ts": _safe_float(row.get("expires_ts")),
                 "next_check_ts": _safe_float(row.get("next_check_ts")),
                 "status": str(row.get("status") or "")[:40],
                 "outcome": str(row.get("outcome") or "")[:48],
                 "reason": str(row.get("reason") or "")[:220],
                 "text": str(row.get("text") or "")}
                for row in source[:limit]]
    except Exception:
        return []


def _read_trades() -> list[dict]:
    rows = []
    try:
        with JOURNAL_FILE.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        rows.append({k: item.get(k) for k in SAFE_TRADE_FIELDS if k in item})
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return rows


def _ts(row: dict, key: str) -> float:
    try:
        value = float(row.get(key) or 0)
        return value if math.isfinite(value) and value > 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _period_bounds(period: str, now: datetime | None = None):
    now = now or datetime.now()
    end = now.timestamp() + 1.0
    key = (period or "today").lower()
    if key in ("all", "all-time", "history"):
        return None, float("inf")
    if key in ("day", "daily", "today"):
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif key in ("week", "weekly"):
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    elif key in ("month", "monthly"):
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        return None, end
    return start.timestamp(), end


def _in_period(ts: float, bounds) -> bool:
    start, end = bounds
    return bool(ts and (start is None or ts >= start) and ts <= end)


def _trade_pips(row: dict):
    try:
        if row.get("pips") not in (None, ""):
            value = float(row["pips"])
            return round(value, 1) if math.isfinite(value) else None
        pip = float(row.get("pip") or 0)
        symbol = str(row.get("symbol") or "").upper()
        if not pip:
            pip = 0.1 if any(tag in symbol for tag in ("XAU", "GOLD")) else 0.0001
        op = float(row.get("open_price") or row.get("price") or 0)
        cp = float(row.get("close_price") or 0)
        if op and cp and all(math.isfinite(x) for x in (pip, op, cp)):
            delta = cp - op
            if str(row.get("direction") or "BUY").upper() == "SELL":
                delta = -delta
            value = delta / pip if pip else float("nan")
            return round(value, 1) if math.isfinite(value) else None
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    return None


def _safe_trade(row: dict) -> dict:
    result = {key: row.get(key) for key in SAFE_TRADE_FIELDS if key in row}
    for key, value in list(result.items()):
        if isinstance(value, (int, float)) and not math.isfinite(float(value)):
            result[key] = None
    pips = _trade_pips(row)
    if pips is not None:
        result["pips"] = pips
    for key in ("placed_ts", "opened_ts", "closed_ts"):
        value = _ts(row, key)
        result[key] = value or None
    try:
        net = float(row.get("net") or 0)
        result["net"] = round(net, 2) if math.isfinite(net) else 0.0
    except (ValueError, TypeError):
        result["net"] = 0.0
    return result


def _range_stats(trades: list[dict], period: str) -> dict:
    bounds = _period_bounds(period)
    selected = [t for t in trades if _in_period(_ts(t, "placed_ts"), bounds)
                or _in_period(_ts(t, "opened_ts"), bounds)
                or _in_period(_ts(t, "closed_ts"), bounds)]
    closed = [t for t in selected if str(t.get("status") or "").lower() == "closed"
              and _in_period(_ts(t, "closed_ts"), bounds)]
    tp = sum(1 for t in closed if str(t.get("result") or "").lower() == "tp")
    sl = sum(1 for t in closed if str(t.get("result") or "").lower() == "sl")
    be = sum(1 for t in closed if str(t.get("result") or "").lower() == "be")
    manual = sum(1 for t in closed if str(t.get("result") or "").lower() == "manual")
    placed = sum(1 for t in trades if _in_period(_ts(t, "placed_ts"), bounds))
    filled = sum(1 for t in trades if _in_period(_ts(t, "opened_ts"), bounds))
    missed = sum(1 for t in trades if str(t.get("status") or "").lower() == "cancelled"
                 and _in_period(_ts(t, "closed_ts") or _ts(t, "placed_ts"), bounds))
    rejected = sum(1 for t in trades if str(t.get("status") or "").lower() == "rejected"
                   and _in_period(_ts(t, "placed_ts"), bounds))
    net = round(sum(float(t.get("net") or 0) for t in closed), 2)
    pips = round(sum(_trade_pips(t) or 0 for t in closed), 1)
    decisions = tp + sl
    opened_now = sum(1 for t in trades if str(t.get("status") or "").lower() == "open"
                      and _in_period(_ts(t, "opened_ts") or _ts(t, "placed_ts"), bounds))
    pending_now = sum(1 for t in trades if str(t.get("status") or "").lower() == "pending"
                       and _in_period(_ts(t, "placed_ts"), bounds))
    return {
        "period": period, "placed": placed, "filled": filled, "closed": len(closed),
        "open": opened_now, "pending": pending_now,
        "missed": missed, "rejected": rejected, "tp": tp, "sl": sl, "be": be,
        "manual": manual, "net": net, "pips": pips,
        "win_rate": round(tp * 100.0 / decisions, 1) if decisions else None,
    }


def _source_rows() -> list[dict]:
    cfg = _engine_literals()
    ids = cfg.get("CHANNEL_IDS") if isinstance(cfg.get("CHANNEL_IDS"), dict) else {}
    id_names = cfg.get("CHANNEL_ID_NAMES") if isinstance(cfg.get("CHANNEL_ID_NAMES"), dict) else {}
    categories = {}
    for name, category in (("LIMIT_CHANNELS", "LIMIT"), ("MARKET_CHANNELS", "MARKET")):
        values = cfg.get(name) or []
        if isinstance(values, str):
            values = [values]
        for item in values:
            key = str(item).strip()
            if key:
                categories[(key, category)] = None
    rows = []
    for key, category in categories:
        chat_id = None
        try:
            chat_id = int(key)
        except ValueError:
            pass
        if chat_id is not None:
            title = str(id_names.get(chat_id) or id_names.get(str(chat_id)) or key)
            mapped = str(ids.get(chat_id) or ids.get(str(chat_id)) or category).upper()
            category = mapped if mapped in ("LIMIT", "MARKET") else category
            rows.append({"name": title, "category": category, "id": chat_id})
        else:
            rows.append({"name": key, "category": category, "id": None})
    for raw_id, raw_category in ids.items():
        try:
            chat_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        category = str(raw_category or "").upper()
        if category not in ("LIMIT", "MARKET"):
            continue
        if any(r["id"] == chat_id for r in rows):
            continue
        title = str(id_names.get(chat_id) or id_names.get(str(chat_id)) or f"Telegram {chat_id}")
        rows.append({"name": title, "category": category, "id": chat_id})
    rows.sort(key=lambda r: (r["category"], r["name"].casefold()))
    return rows


def _rank_sources_by_period(trades: list[dict], period: str) -> list[dict]:
    bounds = _period_bounds(period)
    buckets = {}
    for row in trades:
        if str(row.get("status") or "").lower() != "closed":
            continue
        if not _in_period(_ts(row, "closed_ts"), bounds):
            continue
        name = str(row.get("source") or "Unknown source")
        bucket = buckets.setdefault(name, {"name": name, "orders": 0, "net": 0.0, "tp": 0, "sl": 0})
        bucket["orders"] += 1
        bucket["net"] += float(row.get("net") or 0)
        result = str(row.get("result") or "").lower()
        if result == "tp":
            bucket["tp"] += 1
        elif result == "sl":
            bucket["sl"] += 1
    ranked = sorted(buckets.values(), key=lambda x: x["net"], reverse=True)[:8]
    for item in ranked:
        item["net"] = round(item["net"], 2)
        decided = item["tp"] + item["sl"]
        item["win_rate"] = round(item["tp"] * 100 / decided, 1) if decided else None
    return ranked


def _dashboard_payload() -> dict:
    raw_trades = _read_trades()
    trades = [_safe_trade(t) for t in raw_trades]
    closed_all = [t for t in trades if str(t.get("status") or "").lower() == "closed"
                  and _ts(t, "closed_ts")]
    closed_all.sort(key=lambda t: _ts(t, "closed_ts"))
    net_all = round(sum(float(t.get("net") or 0) for t in closed_all), 2)
    tp = sum(1 for t in closed_all if str(t.get("result") or "").lower() == "tp")
    sl = sum(1 for t in closed_all if str(t.get("result") or "").lower() == "sl")
    decided = tp + sl
    metrics = {key: _range_stats(trades, key) for key in ("today", "week", "month", "all")}
    sources_by_period = {key: _rank_sources_by_period(trades, key)
                         for key in ("all", "today", "week", "month")}
    sources_ranked = sources_by_period["all"]
    status = _status_snapshot()
    status_fresh = bool(status.get("fresh"))
    points, cumulative = [], 0.0
    for row in closed_all[-120:]:
        cumulative += float(row.get("net") or 0)
        points.append({"ts": _ts(row, "closed_ts"), "net": round(cumulative, 2)})
    mt5 = status.get("mt5") if isinstance(status.get("mt5"), dict) else {}
    engine = {
        "online": status_fresh,
        "telegram": bool(status.get("telegram")) if status_fresh else False,
        "who": str(status.get("who") or "") if status_fresh else "",
        "phase": str(status.get("phase") or "") if status_fresh else "",
        "mode": str(status.get("mode") or "UNKNOWN") if status_fresh else "OFFLINE",
        "heartbeat_age": status.get("age_s"),
        "mt5_connected": bool(status_fresh and mt5.get("login")),
    }
    return {
        "app": "EdgeQuant Sentinel", "engine_version": str(_engine_literals().get("VERSION") or VERSION),
        "web_build": WEB_BUILD, "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "engine": engine, "remote": {"configured": False, "state": "NOT CONFIGURED"},
        "metrics": metrics,
        "all_time": {"orders": len(trades), "closed": len(closed_all), "net": net_all,
                     "tp": tp, "sl": sl, "win_rate": round(tp * 100 / decided, 1) if decided else None,
                     "open": sum(1 for t in trades if str(t.get("status") or "").lower() == "open"),
                     "pending": sum(1 for t in trades if str(t.get("status") or "").lower() == "pending")},
        "equity": points, "top_sources": sources_ranked,
        "top_sources_by_period": sources_by_period,
    }


def _csv_bytes(rows: list[dict]) -> bytes:
    columns = [
        "placed_at", "opened_at", "closed_at", "source", "source_type", "symbol", "direction",
        "kind", "order_type", "lot", "sig_entry", "open_price", "close_price", "sl", "tp",
        "status", "result", "pips", "net", "broker", "ticket",
    ]
    def csv_value(value):
        # Prevent channel names/tags from being interpreted as spreadsheet formulas.
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    def stamp(value):
        if not value:
            return ""
        try:
            return datetime.fromtimestamp(float(value)).astimezone().isoformat(timespec="seconds")
        except (TypeError, ValueError, OSError, OverflowError):
            return ""
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        safe = _safe_trade(row)
        safe["placed_at"] = stamp(safe.get("placed_ts"))
        safe["opened_at"] = stamp(safe.get("opened_ts"))
        safe["closed_at"] = stamp(safe.get("closed_ts"))
        writer.writerow({k: csv_value(safe.get(k, "")) for k in columns})
    return buf.getvalue().encode("utf-8-sig")


class WebHandler(BaseHTTPRequestHandler):
    server_version = "EdgeQuantLocalAgent/0.1"
    sys_version = ""

    def _host_allowed(self) -> bool:
        if os.environ.get("EDGEQUANT_WEB_ALLOW_PREVIEW") == "1":
            return True
        host = self.headers.get("Host", "")
        try:
            hostname = urlparse("//" + host).hostname
        except ValueError:
            hostname = None
        return str(hostname or "").lower() in {"localhost", "127.0.0.1", "::1"}

    def log_message(self, fmt, *args):
        # Keep server logs compact; never echo request bodies or credentials.
        print(f"[web] {self.address_string()} {fmt % args}")

    def _headers(self, code: int, content_type: str, length: int):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; base-uri 'none'; form-action 'self'")
        self.end_headers()

    def _send(self, code: int, data: bytes, content_type: str):
        self._headers(code, content_type, len(data))
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, payload, code: int = 200):
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self._send(code, data, "application/json; charset=utf-8")

    def do_GET(self):
        if not self._host_allowed():
            self._send(421, b"Invalid Host header", "text/plain; charset=utf-8")
            return
        parsed = urlparse(self.path)
        route = parsed.path
        if route == "/api/v1/health":
            payload = _dashboard_payload()
            self._json({"ok": True, "agent": "LOCAL READ-ONLY", "engine": payload["engine"],
                        "remote": payload["remote"], "app_home_exists": APP_HOME.is_dir()})
            return
        if route == "/api/v1/dashboard":
            self._json(_dashboard_payload())
            return
        if route == "/api/v1/sources":
            self._json({"sources": _source_rows(), "source_count": len(_source_rows()),
                        "mode": "read-only", "own_posts": "incoming-only"})
            return
        if route in ("/api/v1/channels", "/api/v1/signals", "/api/v1/review", "/api/v1/deferred"):
            params = parse_qs(parsed.query)
            try:
                limit = max(1, min(500, int(params.get("limit", ["100"])[0])))
            except (TypeError, ValueError):
                limit = 100
            if route == "/api/v1/channels":
                monitor = _read_channel_monitor()
                self._json({"channels": monitor["channels"],
                            "updated_ts": monitor["updated_ts"],
                            "agent_online": bool(_status_snapshot().get("fresh")),
                            "mode": "read-only"})
            elif route == "/api/v1/signals":
                self._json({"events": _read_signal_audit(limit), "limit": limit,
                            "mode": "read-only", "raw_text_included": False})
            elif route == "/api/v1/review":
                self._json({"items": _read_review_queue(limit), "limit": limit,
                            "mode": "read-only", "replay_available": False})
            else:
                self._json({"items": _read_deferred_queue(limit), "limit": limit,
                            "mode": "read-only", "replay_available": False})
            return
        if route == "/api/v1/trades":
            rows = [_safe_trade(t) for t in _read_trades()]
            rows.sort(key=lambda t: max(_ts(t, "closed_ts"), _ts(t, "placed_ts")), reverse=True)
            params = parse_qs(parsed.query)
            try:
                limit = max(1, min(500, int(params.get("limit", ["100"])[0])))
            except ValueError:
                limit = 100
            try:
                offset = max(0, int(params.get("offset", ["0"])[0]))
            except ValueError:
                offset = 0
            status_filter = str(params.get("status", ["all"])[0]).strip().lower()[:20]
            query = str(params.get("q", [""])[0]).strip().lower()[:120]
            if status_filter and status_filter != "all":
                rows = [row for row in rows if str(row.get("status") or "").lower() == status_filter]
            if query:
                rows = [row for row in rows if query in " ".join(
                    str(row.get(key) or "") for key in SAFE_TRADE_FIELDS).lower()]
            total = len(rows)
            self._json({"trades": rows[offset:offset + limit], "total": total,
                        "offset": offset, "limit": limit, "status": status_filter,
                        "query": query})
            return
        if route == "/api/v1/export/journal.csv":
            data = _csv_bytes(_read_trades())
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Content-Disposition", 'attachment; filename="edgequant-journal.csv"')
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if route in ("/", "/index.html"):
            try:
                data = INDEX_FILE.read_bytes()
            except OSError:
                self._send(503, b"Web UI is not installed.", "text/plain; charset=utf-8")
                return
            self._send(200, data, "text/html; charset=utf-8")
            return
        if route == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self):
        if not self._host_allowed():
            self._send(421, b"Invalid Host header", "text/plain; charset=utf-8")
            return
        self._json({"ok": False, "error": "Phase 1 is read-only; no trading or settings commands are exposed."}, 405)

    def do_PUT(self):
        self.do_POST()

    def do_DELETE(self):
        self.do_POST()


def run_selftest() -> int:
    failures = []
    checks = 0
    def check(name, got, want):
        nonlocal checks
        checks += 1
        ok = got == want
        print(("PASS" if ok else "FAIL") + f"  {name}")
        if not ok:
            print(f"      got {got!r}\n      want {want!r}")
            failures.append(name)
    check("period stats identify closed P/L separately from placed orders",
          _range_stats([
              {"status": "closed", "result": "tp", "placed_ts": 100,
               "closed_ts": 200, "net": 5},
              {"status": "open", "opened_ts": 200, "placed_ts": 100, "net": 0},
          ], "all")["closed"], 1)
    now = time.time()
    check("all-time P/L is computed only from closed orders",
          _range_stats([
              {"status": "closed", "placed_ts": now - 20, "closed_ts": now - 10, "net": 6},
              {"status": "open", "placed_ts": now - 5, "net": 50},
          ], "all")["net"], 6.0)
    ranking_rows = [
        {"status": "closed", "result": "tp", "source": "Alpha", "closed_ts": now - 60, "net": 7},
        {"status": "closed", "result": "sl", "source": "Alpha", "closed_ts": now - 86400 * 40, "net": -2},
        {"status": "closed", "result": "sl", "source": "Beta", "closed_ts": now - 90, "net": -3},
        {"status": "open", "source": "Ghost", "placed_ts": now - 10, "net": 999},
    ]
    check("best-source ranking defaults to all closed history (no open P/L)",
          (_rank_sources_by_period(ranking_rows, "all")[0]["name"],
           _rank_sources_by_period(ranking_rows, "all")[0]["net"]), ("Alpha", 5.0))
    check("best-source weekly ranking uses closed outcomes from this week",
          [r["name"] for r in _rank_sources_by_period(ranking_rows, "week")], ["Alpha", "Beta"])
    check("source settings can be parsed without executing the engine",
          _json_literal_assignments("LIMIT_CHANNELS = ['Gold']\nMARKET_CHANNELS = []\n")
          .get("LIMIT_CHANNELS"), ["Gold"])
    csv_text = _csv_bytes([{"source": "=1+1", "placed_ts": now, "status": "closed",
                            "closed_ts": now, "net": 1.5}]).decode("utf-8-sig")
    check("CSV export has human-readable timestamps and spreadsheet-formula escaping",
          ("placed_at" in csv_text and "'=1+1" in csv_text,
           datetime.fromtimestamp(now).astimezone().isoformat(timespec="seconds") in csv_text),
          (True, True))
    check("local server rejects write verbs (read-only agent)",
          (hasattr(WebHandler, "do_POST"), any(
              isinstance(value, str) and "trading or settings commands" in value
              for value in WebHandler.do_POST.__code__.co_consts),
           405 in WebHandler.do_POST.__code__.co_consts), (True, True, True))
    check("web assets exist", INDEX_FILE.is_file(), True)
    html = INDEX_FILE.read_text(encoding="utf-8") if INDEX_FILE.is_file() else ""
    get_source = __import__("inspect").getsource(WebHandler.do_GET)
    check("signal monitor uses read-only same-origin endpoints",
          (all(x in html for x in ("/api/v1/channels", "/api/v1/signals", "/api/v1/review", "/api/v1/deferred")),
           "replay_available" in get_source),
          (True, True))
    check("review and deferred APIs are GET-only; writes remain disabled",
          (all(route in get_source for route in
               ("/api/v1/channels", "/api/v1/signals", "/api/v1/review", "/api/v1/deferred")),
           405 in WebHandler.do_POST.__code__.co_consts), (True, True))
    import tempfile
    saved_paths = (CHANNEL_MONITOR_FILE, SIGNAL_AUDIT_FILE, SIGNAL_REVIEW_FILE, SIGNAL_DEFERRED_FILE)
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            globals().update({"CHANNEL_MONITOR_FILE": root / "monitor.json",
                              "SIGNAL_AUDIT_FILE": root / "audit.jsonl",
                              "SIGNAL_REVIEW_FILE": root / "review.jsonl",
                              "SIGNAL_DEFERRED_FILE": root / "deferred.json"})
            (root / "monitor.json").write_text(json.dumps({"updated_ts": now, "channels": {
                "-10042": {"chat_id": -10042, "name": "Test", "category": "LIMIT",
                           "connected": True, "retry_pending": True, "retry_attempts": 1}}}), encoding="utf-8")
            (root / "audit.jsonl").write_text(json.dumps({"ts": now, "event": "decision",
                "source": "Test", "chat_id": -10042, "message_id": 7, "outcome": "blocked",
                "reason": "market closed", "message_hash": "abc123"})+"\n", encoding="utf-8")
            (root / "review.jsonl").write_text(json.dumps({"ts": now, "source": "Test",
                "chat_id": -10042, "message_id": 8, "kind": "unknown_signal",
                "reason": "parse issue", "text": "BUY test\nSL 1", "status": "needs_review"})+"\n", encoding="utf-8")
            (root / "deferred.json").write_text(json.dumps({"signals": [{"id": "id1",
                "created_ts": now, "source": "Test", "chat_id": -10042,
                "message_id": 9, "status": "pending_market_open", "text": "BUY test"}]}), encoding="utf-8")
            result = (_read_channel_monitor()["channels"][0]["chat_id"],
                      _read_signal_audit(10)[0]["outcome"],
                      _read_review_queue(10)[0]["text"],
                      _read_deferred_queue(10)[0]["status"])
            check("local monitor readers preserve negative chat IDs and queue text safely",
                  result, (-10042, "blocked", "BUY test\nSL 1", "pending_market_open"))
    finally:
        globals().update(dict(zip(("CHANNEL_MONITOR_FILE", "SIGNAL_AUDIT_FILE",
                                   "SIGNAL_REVIEW_FILE", "SIGNAL_DEFERRED_FILE"), saved_paths)))
    check("browser calls the same-origin API, not localhost", 
          ("/api/v1/dashboard" in html, "http://localhost" not in html.lower(),
           "credentials:'same-origin'" in html), (True, True, True))
    check("remote sign-in/pairing stays visibly disabled without credentials or external requests",
          ("REMOTE BACKEND · NOT CONFIGURED" in html,
           "no email, password, or auth request is sent" in html,
           "NOT PAIRED" in html,
           html.count('disabled autocomplete="off"') >= 3,
           "https://" not in html.lower(),
           "SUPABASE_ANON_KEY" not in html,
           "service-role key" in html),
          (True, True, True, True, True, True, True))
    print(f"{checks - len(failures)} passed, {len(failures)} failed")
    return 1 if failures else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="EdgeQuant read-only local web agent")
    parser.add_argument("--host", default=os.environ.get("EDGEQUANT_WEB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("EDGEQUANT_WEB_PORT", "8765")))
    parser.add_argument("--open", action="store_true", help="open the local web UI in the default browser")
    parser.add_argument("--selftest", action="store_true", help="run offline web-agent tests")
    args = parser.parse_args(argv)
    if args.selftest:
        return run_selftest()
    if args.port < 1 or args.port > 65535:
        parser.error("--port must be in 1..65535")
    try:
        server = ThreadingHTTPServer((args.host, args.port), WebHandler)
    except OSError as exc:
        print(f"Cannot start EdgeQuant Web Agent: {exc}")
        return 2
    url_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    url = f"http://{url_host}:{args.port}/"
    print("=" * 68)
    print("EdgeQuant Sentinel Web • Phase 2 (local, read-only)")
    print(f"Workspace: {APP_HOME}")
    print(f"URL: {url}")
    print("Remote sync: not configured | Trade controls: disabled")
    print("For a Windows install, keep the server bound to 127.0.0.1.")
    print("=" * 68)
    if args.open:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("Stopping EdgeQuant Web Agent...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
