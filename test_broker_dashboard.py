"""Offline coverage: account-isolated P&L, quote identity, and safe unavailability."""
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

import edgequant_broker_dashboard as D


class BrokerMetricsTests(unittest.TestCase):
    def test_open_floating_all_positions_not_just_bot(self):
        self.assertEqual(D.open_floating([NS(profit=24.55, magic=123),
                                          NS(profit=-9.24, magic=0)]), 15.31)
        self.assertEqual(D.open_floating([]), 0.0)
        self.assertIsNone(D.open_floating(None))

    def test_trading_net_trade_deals_only_excludes_deposits(self):
        deals = [NS(type=0, ticket=1, profit=22.0, commission=-1.4, swap=-0.5, fee=0),
                 NS(type=1, ticket=2, profit=-4, commission=-0.5, swap=0, fee=-0.1),
                 NS(type=2, ticket=3, profit=10000, commission=0, swap=0, fee=0),
                 NS(type=0, ticket=1, profit=22.0, commission=-1.4, swap=-0.5, fee=0)]
        self.assertEqual(D.trading_deal_net(deals), 15.5)
        self.assertEqual(D.trading_deal_net([]), 0.0)
        self.assertIsNone(D.trading_deal_net(None))

    def test_quote_calculated_with_broker_specific_symbol_and_pips(self):
        now = 1762361234.0
        api = Mock()
        api.symbol_info.side_effect = lambda s: NS() if s == 'XAUUSDm' else None
        api.symbol_info_tick.return_value = NS(bid=4001.5, ask=4001.79, time=now, time_msc=0)
        q = D.quote_snapshot(api, ['XAUUSD', 'XAUUSDm'], 0.1, now_ts=now)
        self.assertEqual(q['symbol'], 'XAUUSDm')
        self.assertAlmostEqual(q['spread_pips'], 2.9)
        self.assertEqual(q['status'], 'connected')
        self.assertEqual(D.quote_snapshot(api, ['XAUUSDm'], .1, now_ts=now+70)['status'], 'stale')

    def test_missing_or_invalid_quote_never_guesses_zero_spread(self):
        api = Mock()
        api.symbol_info.return_value = NS()
        api.symbol_info_tick.return_value = None
        self.assertEqual(D.quote_snapshot(api, ['XAUUSD'], .1)['status'], 'unavailable')
        self.assertNotIn('spread_pips', D.quote_snapshot(api, ['XAUUSD'], .1))

    def test_identity_fails_closed_when_login_server_or_path_differ(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = str(Path(folder) / 'terminal64.exe')
            Path(exe).write_text('mock')
            api = Mock()
            api.account_info.return_value = NS(login=111, server='Demo-Server')
            api.terminal_info.return_value = NS(connected=True, path=folder)
            cfg = {'login': '111', 'server': 'Demo-Server', 'path': exe}
            self.assertTrue(D.account_identity_matches(api, cfg))
            for changed in ({'login':'222'}, {'server':'Other-Server'}, {'path':str(Path(folder)/'other.exe')}):
                self.assertFalse(D.account_identity_matches(api, {**cfg, **changed}))
            api.terminal_info.return_value = NS(connected=False, path=folder)
            self.assertFalse(D.account_identity_matches(api, cfg))

    def test_utc_window_derived_from_local_midnight(self):
        stamp = datetime(2026, 11, 5, 13, 25, tzinfo=timezone(timedelta(hours=2)))
        a,b = D.today_utc_window(stamp)
        self.assertLess(a,b)
        self.assertEqual((b-a).total_seconds(), stamp.astimezone().hour*3600 + stamp.astimezone().minute*60)


if __name__ == '__main__':
    unittest.main()
