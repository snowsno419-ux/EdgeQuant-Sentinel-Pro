"""Offline regression tests: NEVER connects to a real MetaTrader account."""
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

import edgequant_auto as E
from edgequant_vip_format import interpret


class FakeMT5:
    TRADE_ACTION_PENDING = 5
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TIME_GTC = 0
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_PLACED = 10008
    TRADE_RETCODE_INVALID_FILL = 10030
    TRADE_RETCODE_INVALID_PRICE = 10015
    TRADE_RETCODE_TIMEOUT = 10012
    def __init__(self, results):
        self.requests = []
        self.results = iter(results)
        self.tick_calls = 0
    def symbol_info(self, symbol):
        return SimpleNamespace(filling_mode=1)
    def symbol_info_tick(self, symbol):
        self.tick_calls += 1
        raise AssertionError('live price lookup not allowed for direct LIMIT dispatch')
    def order_send(self, request):
        self.requests.append(deepcopy(request))
        return next(self.results)
    def last_error(self):
        return 'mock'


class OwnerDirectLimitTests(unittest.TestCase):
    def setUp(self):
        self.br_gold = E.Broker('XAUUSD', digits=2)

    def parse_plan(self, text, category='LIMIT', ask=4000, bid=3999, broker=None):
        s = E.parse_signal(text, default_order_type=category,
                           default_symbol='XAUUSD', fix_direction=False)
        self.assertEqual(s.action, 'place', s.issues)
        return E.build_plan(s, category, broker or self.br_gold, ask, bid)

    def test_fixed_buy_adjustment_ignores_quote_above_or_below(self):
        for quote in (4100, 4300):
            plan = self.parse_plan('GOLD BUY LIMIT 4193 SL 4175 TP 4230', ask=quote,
                                   bid=quote-0.3)
            self.assertEqual(len(plan), 2)
            self.assertEqual([x['type'] for x in plan], ['BUY_LIMIT']*2)
            self.assertEqual([x['price'] for x in plan], [4193.99]*2)
            self.assertEqual([x['sl'] for x in plan], [4175.0, 4175.0])
            self.assertEqual([x['tp'] for x in plan], [4198.99, 4230.0])
            self.assertNotIn('manual_review', [x.get('status') for x in plan])

    def test_sell_two_layers_owner_offset(self):
        plan = self.parse_plan('GOLD SELL LIMIT 4193 SL 4200 TP 4170', ask=4100,bid=4099)
        self.assertEqual([x['type'] for x in plan], ['SELL_LIMIT']*2)
        self.assertEqual([x['price'] for x in plan], [4192.1, 4192.1])
        self.assertEqual([x['sl'] for x in plan], [4200.0, 4200.0])
        self.assertEqual([x['tp'] for x in plan], [4187.1, 4170.0])

    def test_both_protection_levels_missing(self):
        plan = self.parse_plan('GOLD BUY LIMIT 4193')
        self.assertEqual([x['sl'] for x in plan], [4188.99, 4188.99])
        self.assertEqual([x['tp'] for x in plan], [4198.99, 4208.99])
        self.assertEqual(E.incomplete_signal_review_reason(None), '')

    def test_single_missing_sl_or_tp(self):
        only_tp = self.parse_plan('GOLD BUY LIMIT 4193 TP 4210')
        only_sl = self.parse_plan('GOLD BUY LIMIT 4193 SL 4177')
        self.assertEqual(only_tp[1]['sl'], 4188.99)
        self.assertEqual(only_tp[1]['tp'], 4210.0)
        self.assertEqual(only_sl[1]['sl'], 4177.0)
        self.assertEqual(only_sl[1]['tp'], 4208.99)

    def test_dashboard_custom_layer1_target_and_shared_signal_sl(self):
        s = E.parse_signal('GOLD SELL LIMIT 4067 SL 4070 TP 4020',
                           default_order_type='LIMIT', default_symbol='XAUUSD')
        plan = E.build_plan(s, 'LIMIT', self.br_gold, 4000.0, 3999.0,
                            quick_tp_pips=75.0)
        self.assertEqual([x['price'] for x in plan], [4066.10, 4066.10])
        self.assertEqual([x['sl'] for x in plan], [4070.0, 4070.0])
        self.assertEqual([x['tp'] for x in plan], [4058.6, 4020.0])

    def test_separate_gold_range_levels_two_layers_each(self):
        plan = self.parse_plan('GOLD SELL LIMIT 4065-4070 SL 4075 TP 4040',
                               ask=4068, bid=4067)
        self.assertEqual(len(plan), 4)
        self.assertEqual([x['price'] for x in plan], [4064.1,4064.1,4069.1,4069.1])
        self.assertEqual([x['sl'] for x in plan], [4075.0]*4)

    def test_legacy_non_object_journal_rows_are_ignored(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            with patch.object(E, 'HERE', Path(d)), patch.object(E, 'TRADE_LOG','test-trades.jsonl'):
                (Path(d)/'test-trades.jsonl').write_text('"bad record"\n{"ticket":123,"status":"pending"}\n', encoding='utf-8')
                E.jr_load()
                self.assertEqual(len(E.TRADES), 1)
                self.assertEqual(E.TRADES[0]['ticket'], 123)

    def test_forex_pip_size(self):
        br = E.Broker('EURUSD', digits=5, point=0.00001, tick_size=0.00001)
        plan = self.parse_plan('EURUSD SELL LIMIT 1.10450',
                               category='LIMIT',broker=br)
        self.assertEqual([x['price'] for x in plan], [1.1045, 1.1045])
        self.assertEqual([x['sl'] for x in plan], [1.1095, 1.1095])
        self.assertEqual([x['tp'] for x in plan], [1.0995, 1.0895])

    def test_vip_without_protection_accepted(self):
        for text in ('GOLD BUY 4193', 'GOLD BUY 4193 SL 4188',
                     'GOLD BUY 4193 TP 4205', 'GOLD BUY 4193 SL 4188 TP 4205'):
            v = interpret(text, channel_id=-11, message_id=121,
                          enabled_channel_ids=(-11,))
            self.assertEqual(v.kind, 'signal', text)

    def test_stale_price_hit_does_not_skip_limit(self):
        s = E.parse_signal('GOLD BUY LIMIT 4193 SL 4183 TP 4210',
                           default_order_type='LIMIT')
        s.msg_ts = 1
        self.assertEqual(E.stale_signal(s, 4500, 4499, category='LIMIT'), (False, ''))

    def test_two_sends_no_quote_check(self):
        plan = self.parse_plan('GOLD BUY LIMIT 4193')
        api = FakeMT5([SimpleNamespace(retcode=10008, order=135),
                       SimpleNamespace(retcode=10008, order=136)])
        with patch.object(E, 'mt5', api), patch.object(E, 'DRY_RUN', False):
            tickets = E.execute_plan(plan, 'XAUUSD')
        self.assertEqual(tickets, [135,136])
        self.assertEqual(api.tick_calls, 0)
        self.assertEqual(len(api.requests), 2)
        self.assertEqual([req['price'] for req in api.requests],[4193.99,4193.99])
        self.assertEqual([req['sl'] for req in api.requests],[4188.99,4188.99])
        self.assertEqual([req['tp'] for req in api.requests],[4198.99,4208.99])
        self.assertEqual([x['status'] for x in plan],['pending','pending'])

    def test_rejection_does_not_wait_for_approval(self):
        plan = self.parse_plan('GOLD BUY LIMIT 4193')
        api = FakeMT5([SimpleNamespace(retcode=10015, order=0,
                                      comment='Invalid price'),
                       SimpleNamespace(retcode=10008, order=136)])
        with patch.object(E, 'mt5', api), patch.object(E, 'DRY_RUN', False):
            tickets = E.execute_plan(plan, 'XAUUSD')
        self.assertEqual(tickets, [136])
        self.assertEqual([x['status'] for x in plan],['rejected','pending'])
        self.assertEqual(len(api.requests), 2)

    def test_ambiguous_receipt_stops_to_prevent_duplicate(self):
        plan = self.parse_plan('GOLD BUY LIMIT 4193')
        api = FakeMT5([None])
        with patch.object(E, 'mt5', api), patch.object(E, 'DRY_RUN', False):
            tickets = E.execute_plan(plan,'XAUUSD')
        self.assertEqual(tickets, [])
        self.assertEqual([x['status'] for x in plan], ['uncertain', 'not_attempted'])
        self.assertEqual(len(api.requests), 1)

    def test_market_now_not_coerced_into_pending(self):
        s = E.parse_signal('GOLD BUY NOW 4193', default_order_type='MARKET')
        self.assertFalse(E.uses_direct_limit(s,'MARKET'))

if __name__ == '__main__':
    unittest.main()
