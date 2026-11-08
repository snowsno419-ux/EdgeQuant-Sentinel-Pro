"""Persistent, one-shot GOLD LIMIT VIP virtual-entry watch records.

This module deliberately never connects to MT5 or sends an order. It persists
precise original-chat + broker + entry keys and validates the entry touch. The
engine alone applies risk controls and performs trade execution. A durable
claim is written BEFORE any market submission; uncertain results are never
retried automatically.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path

WATCH_MAX_SECONDS = 2 * 60 * 60  # no stale overnight entries
WATCH_TOUCH_PIPS = 1.0           # XAUUSD: 0.1 price units


def watch_key(chat_id, message_id, broker, login, server, src_price):
    identity = (f"{int(chat_id)}|{int(message_id)}|{str(broker).upper()}|"
                f"{int(login)}|{str(server).casefold()}|{float(src_price):.8f}")
    return hashlib.sha256(identity.encode('utf-8')).hexdigest()


def record_path(folder, key):
    if not isinstance(key, str) or len(key) != 64 or not all(c in '0123456789abcdef' for c in key):
        raise ValueError('invalid watch record key')
    return Path(folder) / (key + '.json')


def store_new(folder, record):
    """One exact chat + message + account + source level cannot be rearmed."""
    if str(record.get('source', '')).strip().casefold() != 'gold limit vip':
        raise ValueError('virtual market fallback is GOLD LIMIT VIP only')
    if not (int(record.get('chat_id') or 0) and int(record.get('message_id') or 0)):
        raise ValueError('exact Telegram identity is required')
    if len(record.get('orders') or []) != 2:
        raise ValueError('virtual market fallback must have exactly two layers')
    key = watch_key(record['chat_id'], record['message_id'], record['broker'],
                    record['login'], record['server'], record['src_price'])
    data = dict(record)
    data.update({'id': key, 'version': 1, 'status': 'waiting',
                 'created_ts': time.time(), 'expires_ts': time.time() + WATCH_MAX_SECONDS})
    for n, o in enumerate(data['orders'], 1):
        if str(o.get('kind')) != 'WATCH_MARKET' or str(o.get('type')) not in ('BUY', 'SELL'):
            raise ValueError('watch record may contain only guarded BUY/SELL market layers')
        if float(o.get('price') or 0) <= 0 or float(o.get('lot') or 0) <= 0:
            raise ValueError('watch record missing entry or volume')
        o['layer'] = n
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = record_path(folder, key)
    try:
        with path.open('x', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            fh.flush()
            os.fsync(fh.fileno())
    except FileExistsError:
        return None  # do not rearm after claimed, expired, or a restart
    return path


def load(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('version') != 1:
            return None
        if record_path(Path(path).parent, data['id']) != Path(path):
            return None
        return data
    except (ValueError, OSError, KeyError, TypeError):
        return None


def active(folder, *, chat_id=None, message_id=None):
    folder = Path(folder)
    for p in folder.glob('*.json') if folder.is_dir() else ():
        rec = load(p)
        if not rec or rec.get('status') != 'waiting':
            continue
        if chat_id is not None and int(rec.get('chat_id') or 0) != int(chat_id):
            continue
        if message_id is not None and int(rec.get('message_id') or 0) != int(message_id):
            continue
        yield p, rec


def update(path, data):
    """Replace receipt atomically (one engine process manages mutations)."""
    path = Path(path)
    tmp = path.with_suffix('.json.' + str(os.getpid()) + '.tmp')
    try:
        with tmp.open('w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            fh.flush()
            os.fsync(fh.fileno())
        tmp.replace(path)
    finally:
        try: tmp.unlink(missing_ok=True)
        except OSError: pass


def claim(path):
    """EXCLUSIVE durable one-shot marker: never replay after crash/timeout."""
    claim_path = Path(path).with_suffix('.claim')
    try:
        with claim_path.open('x', encoding='utf-8') as fh:
            fh.write(str(time.time()))
            fh.flush()
            os.fsync(fh.fileno())
        return True
    except (FileExistsError, OSError):
        return False


def at_first_touch(side, level, bid, ask, pip_size, *, touch_pips=WATCH_TOUCH_PIPS):
    """Quote must be AT exact adjusted entry (within one XAU pip).

    Crossed prices outside the tolerance are NOT chased at market; a later
    return into the band is required. BUY uses Ask, SELL uses Bid.
    """
    try:
        nums = (level, bid, ask, pip_size, touch_pips)
        if not all(math.isfinite(float(x)) for x in nums): return False
        level, bid, ask, pip_size, touch_pips = map(float, nums)
        if min(level, bid, ask, pip_size) <= 0 or ask < bid or touch_pips < 0: return False
        quote = ask if side == 'BUY' else bid if side == 'SELL' else 0.0
        return bool(quote and abs(quote - level) <= pip_size * touch_pips + 1e-8)
    except (TypeError, ValueError, OverflowError):
        return False


def protected_pair_at_quote(orders, direction, bid, ask, min_distance, tick_size):
    """Both exact TPs and protective SLs must be broker-valid BEFORE claim."""
    try:
        if len(orders) != 2 or direction not in ('BUY', 'SELL'):
            return False, 'not a valid two-layer market pair'
        nums = [bid, ask, min_distance, tick_size]
        if not all(math.isfinite(float(x)) for x in nums):
            return False, 'nonfinite broker quote/spec'
        bid, ask, distance, grid = map(float, nums)
        if bid <= 0 or ask < bid or distance < 0 or grid <= 0:
            return False, 'broker quote or tick size missing'
        price = ask if direction == 'BUY' else bid
        for o in orders:
            if o.get('kind') != 'WATCH_MARKET' or o.get('type') != direction:
                return False, 'layer direction or market fallback kind mismatch'
            if float(o.get('lot') or 0) <= 0 or not math.isfinite(float(o.get('lot') or 0)):
                return False, 'invalid lot'
            sl, tp = float(o.get('sl') or 0), float(o.get('tp') or 0)
            if sl <= 0 or tp <= 0 or not all(math.isfinite(v) for v in (sl, tp)):
                return False, 'both market layers require valid protective SL and TP'
            if abs(sl / grid - round(sl / grid)) > 1e-5 or abs(tp / grid - round(tp / grid)) > 1e-5:
                return False, 'signal SL/TP not on broker tick grid'
            # Quote-side preflight. Broker still has final say during DEAL.
            if direction == 'BUY' and not (sl < price - distance and tp > price + distance):
                return False, 'BUY SL/TP wrong side or inside minimum stop distance'
            if direction == 'SELL' and not (sl > price + distance and tp < price - distance):
                return False, 'SELL SL/TP wrong side or inside minimum stop distance'
        return True, ''
    except (TypeError, ValueError, OverflowError):
        return False, 'invalid watch order fields'
