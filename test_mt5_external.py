"""Offline tests for non-EdgeQuant MT5 importing and guarded local edits.

Run with: python test_mt5_external.py
No MT5 terminal, broker login, or order is required.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import edgequant_auto as E


class SnapshotApi:
    POSITION_TYPE_BUY = 0
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1
    DEAL_ENTRY_INOUT = 2
    DEAL_ENTRY_OUT_BY = 3
    DEAL_TYPE_BUY = 0
    DEAL_REASON_SL = 4
    DEAL_REASON_TP = 5

    def __init__(self, positions, orders, today_deals, history):
        self._positions = list(positions)
        self._orders = list(orders)
        self._today_deals = list(today_deals)
        self._history = dict(history)

    def positions_get(self, **_kwargs):
        return list(self._positions)

    def orders_get(self, **_kwargs):
        return list(self._orders)

    def history_deals_get(self, *args, **kwargs):
        if "position" in kwargs:
            return list(self._history.get(int(kwargs["position"]), []))
        return list(self._today_deals)


def _deal(pid, ticket, when, *, entry, magic=0, profit=0.0,
          commission=0.0, swap=0.0, fee=0.0, reason=0, typ=0,
          symbol="EURUSD", order=0, price=1.1, volume=0.1):
    return SimpleNamespace(position_id=pid, ticket=ticket, order=order or ticket,
                           time=when, entry=entry, magic=magic, profit=profit,
                           commission=commission, swap=swap, fee=fee,
                           reason=reason, type=typ, symbol=symbol,
                           price=price, volume=volume, sl=0.0, tp=0.0)


def test_external_snapshot_daily_exits_and_today_only_rows():
    now = datetime.now().astimezone()
    today = now.timestamp()
    older = (now - timedelta(days=2)).timestamp()
    opened_today = SimpleNamespace(
        ticket=500, identifier=500, magic=1234, type=0, symbol="EURUSD",
        volume=0.10, price_open=1.0800, price_current=1.0850, sl=1.0700,
        tp=1.0900, profit=5.0, time=today)
    edgequant_position = SimpleNamespace(
        ticket=600, identifier=600, magic=E.MAGIC, type=0, symbol="EURUSD",
        volume=0.10, price_open=1.0800, price_current=1.0850, sl=1.0700,
        tp=1.0900, profit=99.0, time=today)
    pending_today = SimpleNamespace(
        ticket=700, magic=4321, type=2, symbol="EURUSD", volume_current=0.20,
        volume_initial=0.20, price_open=1.0750, price=1.0750, sl=1.0700,
        tp=1.0900, time=today, time_setup=today)

    old_entry = _deal(123, 1001, older, entry=0, magic=1234, profit=0.0)
    close_today = _deal(123, 1002, today, entry=1, magic=1234, profit=20.0,
                        commission=-1.0, swap=-0.25, fee=-0.10, reason=5)
    edge_close = _deal(600, 1003, today, entry=1, magic=E.MAGIC,
                       profit=99.0, reason=5)
    journal_close = _deal(777, 1004, today, entry=1, magic=0,
                          profit=50.0, reason=0)
    api = SnapshotApi(
        [opened_today, edgequant_position], [pending_today],
        [close_today, edge_close, journal_close],
        {123: [old_entry, close_today], 500: [], 600: [edge_close],
         777: [journal_close]},
    )
    snapshot = E.mt5_external_trade_snapshot(
        api, broker="MAIN", now=now,
        journal_trades=[{"ticket": 888, "position_id": 777, "broker": "MAIN"}],
    )

    assert snapshot["status"] == "connected"
    assert snapshot["net_today"] == 18.65  # includes the prior-day position's exit
    assert snapshot["float"] == 5.0       # EdgeQuant floating is excluded
    assert snapshot["closed_today"] == 1
    assert snapshot["open_today"] == 1
    assert snapshot["pending_today"] == 1
    assert snapshot["deal_count"] == 1
    assert {row["ticket"] for row in snapshot["trades"]} == {500, 700}
    assert all(row["broker"] == "MAIN" for row in snapshot["trades"])


def test_mt5_account_history_is_complete_and_channel_attributed():
    now = datetime.now().astimezone().timestamp()
    entry = _deal(77, 9001, now - 600, entry=0, magic=E.MAGIC,
                  commission=-0.5, typ=0, order=8100, price=1.1000)
    exit_ = _deal(77, 9002, now - 300, entry=1, magic=E.MAGIC,
                  profit=8.0, commission=-0.5, reason=5, typ=1,
                  order=8101, price=1.1080)
    ext_in = _deal(88, 9011, now - 500, entry=0, magic=0,
                   typ=0, order=8200, price=1.2000)
    ext_out = _deal(88, 9012, now - 250, entry=1, magic=0,
                    profit=-3.0, commission=-0.2, typ=1,
                    order=8201, price=1.1970)
    active = SimpleNamespace(ticket=99, identifier=99, magic=E.MAGIC,
        type=0, symbol="EURUSD", volume=0.2, price_open=1.09,
        price_current=1.10, sl=1.08, tp=1.12, profit=2.0, time=now - 60)
    account = SimpleNamespace(balance=1004.0, equity=1006.0, currency="USD",
                              name="Main", company="Broker", login=123)

    class HistoryApi:
        DEAL_ENTRY_IN = 0
        DEAL_ENTRY_OUT = 1
        DEAL_ENTRY_INOUT = 2
        DEAL_ENTRY_OUT_BY = 3
        DEAL_TYPE_BUY = 0
        POSITION_TYPE_BUY = 0
        DEAL_REASON_TP = 5
        DEAL_REASON_SL = 4

        def account_info(self):
            return account

        def positions_get(self):
            return [active]

        def history_deals_get(self, _start, _end):
            return [entry, exit_, ext_in, ext_out]

    snapshot = E.mt5_account_history_snapshot(
        HistoryApi(), broker="MAIN", journal_trades=[{
            "ticket": 8100, "position_id": 77, "source": "TEST LIMIT CHANNEL",
            "source_type": "LIMIT", "broker": "MAIN", "signal_ts": now - 700,
            "placed_ts": now - 650,
        }])
    assert snapshot["status"] == "connected"
    assert snapshot["balance"] == 1004.0 and snapshot["equity"] == 1006.0
    assert snapshot["currency"] == "USD" and snapshot["deal_count"] == 4
    by_pid = {row["position_id"]: row for row in snapshot["trades"]}
    assert by_pid[77]["source"] == "TEST LIMIT CHANNEL"
    assert by_pid[77]["source_type"] == "LIMIT"
    assert by_pid[77]["net"] == 7.0 and by_pid[77]["result"] == "tp"
    assert by_pid[77]["signal_ts"] == now - 700
    assert by_pid[88]["source"] == "MT5 Manual / Other EA"
    assert by_pid[88]["net"] == -3.2 and by_pid[88]["status"] == "CLOSED"
    assert by_pid[99]["status"] == "OPEN" and by_pid[99]["floating"] == 2.0


def test_external_snapshot_merge_sums_accounts_without_losing_rows():
    a = {"status": "connected", "broker": "A", "net_today": 2.5,
         "float": -1.0, "closed_today": 1, "open_today": 2,
         "pending_today": 1, "deal_count": 3,
         "trades": [{"ticket": 10, "broker": "A", "opened_ts": 20}],
         "manage_rows": []}
    b = {"status": "connected", "broker": "B", "net_today": 4.0,
         "float": 3.0, "closed_today": 2, "open_today": 1,
         "pending_today": 0, "deal_count": 4,
         "trades": [{"ticket": 10, "broker": "B", "opened_ts": 30}],
         "manage_rows": []}
    merged = E.mt5_merge_external_snapshots([a, b, {"status": "unavailable"}])
    assert merged["net_today"] == 6.5
    assert merged["float"] == 2.0
    assert merged["closed_today"] == 3
    assert merged["accounts"] == ["A", "B"]
    assert [(r["broker"], r["ticket"]) for r in merged["trades"]] == [
        ("B", 10), ("A", 10)]


class EditApi:
    POSITION_TYPE_BUY = 0
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    TRADE_ACTION_MODIFY = 7
    TRADE_ACTION_SLTP = 6
    ORDER_TIME_GTC = 0
    TRADE_RETCODE_DONE = 10009

    def __init__(self):
        self.position = SimpleNamespace(
            ticket=1, symbol="EURUSD", type=0, price_open=1.0,
            price_current=1.1, sl=0.9, tp=1.2, volume=0.1)
        self.order = SimpleNamespace(
            ticket=2, symbol="EURUSD", type=3, price_open=1.2, price=1.2,
            sl=1.3, tp=1.1, volume_current=0.1, volume_initial=0.1,
            type_time=0, time_expiration=0, price_stoplimit=0.0)
        self.requests = []

    def terminal_info(self):
        return object()

    def positions_get(self, ticket=None):
        return [self.position] if ticket in (None, 1) else []

    def orders_get(self, ticket=None):
        return [self.order] if ticket in (None, 2) else []

    def symbol_info_tick(self, _symbol):
        return SimpleNamespace(bid=1.1, ask=1.1002)

    def order_send(self, request):
        self.requests.append(dict(request))
        return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, comment="done")


def test_guarded_ticket_edits_and_profit_only_break_even():
    saved = {name: getattr(E, name) for name in
             ("mt5", "HAVE_MT5", "DRY_RUN", "TRADES", "_JR_LOADED",
              "broker_names", "mt5_ready")}
    api = EditApi()
    E.mt5 = api
    E.HAVE_MT5 = True
    E.DRY_RUN = False
    E.TRADES = []
    E._JR_LOADED = False
    E.broker_names = lambda: ["MAIN"]
    E.mt5_ready = lambda: True
    try:
        blocked = E.mt5_edit_ticket(1, order_type="OPEN", sl=0.0)
        assert not blocked["ok"] and "Removing an existing SL" in blocked["message"]
        assert not api.requests

        result = E.mt5_edit_ticket(1, order_type="OPEN", sl=1.01, tp=1.2)
        assert result["ok"]
        assert api.requests[-1]["action"] == api.TRADE_ACTION_SLTP
        assert api.requests[-1]["position"] == 1
        assert api.requests[-1]["sl"] == 1.01

        api.position.sl = 0.9
        be = E.mt5_edit_ticket(1, order_type="OPEN", move_be=True)
        assert be["ok"] and api.requests[-1]["sl"] == 1.0
        api.position.sl = 1.0
        already_safe = E.mt5_edit_ticket(1, order_type="OPEN", move_be=True)
        assert not already_safe["ok"] and "already at or beyond break-even" in already_safe["message"]

        pending = E.mt5_edit_ticket(2, order_type="PENDING", entry=1.25)
        assert pending["ok"]
        assert api.requests[-1]["action"] == api.TRADE_ACTION_MODIFY
        assert api.requests[-1]["order"] == 2
        assert api.requests[-1]["price"] == 1.25
    finally:
        for name, value in saved.items():
            setattr(E, name, value)


def main():
    tests = [test_external_snapshot_daily_exits_and_today_only_rows,
             test_external_snapshot_merge_sums_accounts_without_losing_rows,
             test_mt5_account_history_is_complete_and_channel_attributed,
             test_guarded_ticket_edits_and_profit_only_break_even]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
