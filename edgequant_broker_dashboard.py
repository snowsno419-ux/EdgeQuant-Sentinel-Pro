"""Read-only account-specific MT5 dashboard calculations and quote-only sidecar.

No trade API operations are used. Quote sidecars run in separate Python processes,
so reading broker B never reselects broker B in the trading engine's MT5 connector.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def today_utc_window(now=None):
    """Midnight in the Windows server's local timezone, expressed as UTC-naive MT5 dates."""
    current = datetime.now().astimezone() if now is None else now.astimezone()
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    return (start.astimezone(timezone.utc).replace(tzinfo=None),
            current.astimezone(timezone.utc).replace(tzinfo=None))


def trading_deal_net(deals, buy_type=0, sell_type=1):
    """Today's net of BUY/SELL deal records; never count deposits/withdrawals as profit.

    Return None for a failed history query. Opening trade commissions are included,
    so the display calls this TODAY TRADING NET rather than exclusively closed P&L.
    """
    if deals is None:
        return None
    result = 0.0
    seen = set()
    for d in deals:
        try:
            kind = int(getattr(d, 'type', -999))
            if kind not in (int(buy_type), int(sell_type)):
                continue
            ticket = int(getattr(d, 'ticket', 0) or 0)
            if ticket and ticket in seen:
                continue
            if ticket:
                seen.add(ticket)
            result += sum(float(getattr(d, key, 0) or 0.0)
                          for key in ('profit', 'commission', 'swap', 'fee'))
        except (TypeError, ValueError, OverflowError):
            continue
    return round(result, 2) if math.isfinite(result) else None


def open_floating(positions):
    """Floating P&L from every open position in this account, not only bot-magic trades."""
    if positions is None:
        return None
    total = 0.0
    try:
        for pos in positions:
            total += float(getattr(pos, 'profit', 0.0) or 0.0)
    except (TypeError, ValueError, OverflowError):
        return None
    return round(total, 2) if math.isfinite(total) else None


def quote_snapshot(api, symbols, pip_unit=0.1, now_ts=None):
    """Choose the broker's own GOLD symbol and read its last tick without account switching."""
    now_ts = float(time.time() if now_ts is None else now_ts)
    pip_unit = float(pip_unit or 0)
    if pip_unit <= 0:
        return {'status': 'unavailable', 'reason': 'invalid GOLD pip size'}
    for symbol in dict.fromkeys(str(s or '').strip() for s in (symbols or []) if str(s or '').strip()):
        try:
            spec = api.symbol_info(symbol)
            if spec is None:
                continue
            # No symbols are selected or modified by this read-only dashboard.
            tick = api.symbol_info_tick(symbol)
            if tick is None:
                continue
            bid, ask = float(getattr(tick, 'bid', 0) or 0), float(getattr(tick, 'ask', 0) or 0)
            if not (math.isfinite(bid) and math.isfinite(ask) and 0 < bid <= ask):
                continue
            ts = float(getattr(tick, 'time_msc', 0) or 0) / 1000
            if not ts:
                ts = float(getattr(tick, 'time', 0) or 0)
            if not ts:
                return {'status': 'stale', 'symbol': symbol, 'reason': 'tick timestamp missing'}
            spread_price = ask - bid
            return {'status': 'stale' if now_ts - ts > 30 or ts > now_ts + 60 else 'connected',
                    'symbol': symbol, 'bid': bid, 'ask': ask, 'spread_price': round(spread_price, 6),
                    'spread_pips': round(spread_price / pip_unit, 3), 'tick_ts': ts,
                    'updated_ts': now_ts}
        except (AttributeError, TypeError, ValueError, OverflowError):
            continue
    return {'status': 'unavailable', 'reason': 'No valid GOLD tick for this broker',
            'updated_ts': now_ts}


def account_identity_matches(api, config):
    """Prevent a quote sidecar from showing another account's quotes under this broker."""
    account, terminal = api.account_info(), api.terminal_info()
    if account is None or terminal is None or getattr(terminal, 'connected', None) is False:
        return False
    try:
        actual_login = int(getattr(account, 'login', 0) or 0)
        expected_login = int(config.get('login') or 0)
        actual_server = str(getattr(account, 'server', '') or '').casefold()
        expected_server = str(config.get('server') or '').casefold()
        if not expected_login or actual_login != expected_login or not expected_server or actual_server != expected_server:
            return False
        term_path = str(getattr(terminal, 'path', '') or '')
        exe = term_path if term_path.lower().endswith('.exe') else str(Path(term_path) / 'terminal64.exe')
        return os.path.normcase(os.path.abspath(exe)) == os.path.normcase(os.path.abspath(config['path']))
    except (TypeError, ValueError, KeyError):
        return False


def quote_worker():
    """Start with --quote-worker. Config arrives on stdin, never in the process args.

    Maintains a single MT5 connection; emits JSON lines and never sends orders.
    """
    config = json.loads(sys.stdin.readline())
    name = str(config.get('name') or '').strip()
    path = str(config.get('path') or '').strip()
    if not name or not path or not Path(path).is_file():
        return 2
    try:
        import MetaTrader5 as mt5
    except ImportError:
        print(json.dumps({'name': name, 'status': 'unavailable', 'reason': 'MetaTrader5 not installed'}), flush=True)
        return 2
    initialized = False
    last_connect_attempt = 0.0
    last_history_read = 0.0
    cached_today_net = None
    try:
        while True:
            now = time.time()
            try:
                if not initialized and now - last_connect_attempt >= 10.0:
                    last_connect_attempt = now
                    initialized = bool(mt5.initialize(path=path))
                if initialized and account_identity_matches(mt5, config):
                    quote = quote_snapshot(mt5, config.get('symbols') or [],
                                           config.get('pip_unit', 0.1), now_ts=now)
                    try:
                        positions = mt5.positions_get()
                        quote['floating_total'] = open_floating(positions)
                        acc = mt5.account_info()
                        if acc is not None:
                            quote['balance'] = float(getattr(acc, 'balance', 0) or 0)
                            quote['equity'] = float(getattr(acc, 'equity', 0) or 0)
                            quote['currency'] = str(getattr(acc, 'currency', '') or '')
                    except Exception:
                        quote['floating_total'] = None
                    if not last_history_read or now - last_history_read >= 15:
                        try:
                            from_utc, to_utc = today_utc_window()
                            trades = mt5.history_deals_get(from_utc, to_utc)
                            cached_today_net = trading_deal_net(
                                trades, getattr(mt5, 'DEAL_TYPE_BUY', 0),
                                getattr(mt5, 'DEAL_TYPE_SELL', 1))
                        except Exception:
                            cached_today_net = None
                        last_history_read = now
                    quote['today_net'] = cached_today_net
                else:
                    cached_today_net = None
                    last_history_read = 0.0
                    quote = {'status': 'not_connected',
                             'reason': 'MT5 terminal/login/server identity is not connected or mismatched'}
                    if initialized:
                        mt5.shutdown()
                        initialized = False
                print(json.dumps({'name': name, **quote, 'received_ts': now}), flush=True)
            except Exception as exc:
                print(json.dumps({'name': name, 'status': 'unavailable',
                                  'reason': f'{type(exc).__name__}: {exc}', 'received_ts': now}), flush=True)
                initialized = False
                try:
                    mt5.shutdown()
                except Exception:
                    pass
            time.sleep(2.5)
    except (BrokenPipeError, KeyboardInterrupt, EOFError):
        return 0
    finally:
        if initialized:
            try:
                mt5.shutdown()
            except Exception:
                pass


if __name__ == '__main__' and '--quote-worker' in sys.argv:
    sys.exit(quote_worker())
