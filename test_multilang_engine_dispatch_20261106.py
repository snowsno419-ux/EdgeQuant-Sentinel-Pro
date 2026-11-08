"""Mock MT5 dispatch tests: no real orders or network calls."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import edgequant_auto as E
from test_scoped_multilingual_signal_updates_20261106 import rows


class Dispatch(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

    def test_exact_reply_updates_only_parent_both_layers_and_dedups(self):
        trades = rows() + rows(message_id=56, broker='SECOND', entry=4000)
        calls = []
        def fake_edit(ticket, **kwargs):
            calls.append((ticket, kwargs))
            return {'ok': True, 'ticket': ticket}
        with (patch.object(E, 'TRADES', trades),
              patch.object(E, 'HERE', Path(self.tempdir.name)),
              patch.object(E, 'DRY_RUN', False),
              patch.object(E, 'HAVE_MT5', True),
              patch.object(E, 'mt5_ready', return_value=True),
              patch.object(E, 'mt5_edit_ticket', fake_edit),
              patch.object(E, 'jr_save'), patch.object(E, 'jr_write_files'),
              patch.object(E, 'signal_audit'), patch.object(E, 'log')):
            self.assertTrue(E.apply_telegram_scoped_signal_update(
                'entry eka 4050ta ganna sl eka 4000ta tiyananna',
                'A GOLD CHANNEL', 10, 97, 'LIMIT', reply_to_id=55))
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][1]['entry'], 4050.99)
            self.assertEqual(calls[0][1]['sl'], 4000)
            self.assertEqual(trades[0]['sig_entry'], 4050)
            self.assertEqual(trades[2]['sig_entry'], 4000)
            # Same Telegram reply after reconnect must be exactly-once.
            self.assertTrue(E.apply_telegram_scoped_signal_update(
                'entry eka 4050ta ganna sl eka 4000ta tiyananna',
                'A GOLD CHANNEL', 10, 97, 'LIMIT', reply_to_id=55))
            self.assertEqual(len(calls), 2)

    def test_original_edit_full_signal_scoped_to_exact_id(self):
        trades = rows()
        calls = []
        with (patch.object(E, 'TRADES', trades), patch.object(E, 'HERE', Path(self.tempdir.name)),
              patch.object(E, 'DRY_RUN', False), patch.object(E, 'HAVE_MT5', True),
              patch.object(E, 'mt5_ready', return_value=True),
              patch.object(E, 'mt5_edit_ticket', side_effect=lambda ticket, **kw: (calls.append((ticket, kw)) or {'ok':True})),
              patch.object(E, 'jr_save'), patch.object(E, 'jr_write_files'),
              patch.object(E, 'signal_audit'), patch.object(E, 'log')):
            self.assertTrue(E.apply_telegram_scoped_signal_update(
                'GOLD BUY 4050 SL 4000 TP 4100', 'A GOLD CHANNEL',10,55,'LIMIT',edited_original=True))
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[1][1]['tp'], None)  # TP 4100 unchanged
            self.assertEqual(trades[1]['sig_entry'],4050)

    def test_unknown_full_signal_reply_is_not_swallowed(self):
        with patch.object(E, 'TRADES', []):
            self.assertFalse(E.apply_telegram_scoped_signal_update(
                'GOLD BUY 4050 SL 4000 TP 4100', 'A GOLD CHANNEL',10,100,'LIMIT',reply_to_id=10))

    def test_failed_mt5_edit_not_written_as_updated(self):
        trades = rows()
        with (patch.object(E, 'TRADES', trades), patch.object(E, 'HERE', Path(self.tempdir.name)),
              patch.object(E, 'DRY_RUN', False), patch.object(E, 'HAVE_MT5', True),
              patch.object(E, 'mt5_ready', return_value=True),
              patch.object(E, 'mt5_edit_ticket', return_value={'ok':False,'message':'invalid stops'}),
              patch.object(E, 'jr_save'), patch.object(E, 'jr_write_files'),
              patch.object(E, 'signal_audit'), patch.object(E, 'log')):
            self.assertTrue(E.apply_telegram_scoped_signal_update(
                'move entry to 4050 sl 4000', 'A GOLD CHANNEL',10,99,'LIMIT',reply_to_id=55))
            self.assertEqual(trades[0]['sig_entry'],4000)

if __name__=='__main__':
    unittest.main()

class FakeOrder:
    ticket = 200
    symbol = 'XAUUSDm'
    type = 2  # BUY LIMIT
    price_open = 4000.99
    sl = 3950.0
    tp = 4005.99
    type_time = 0
    time_expiration = 0
    magic = 190912
    price_stoplimit = 0


class FakeActualMT5:
    TRADE_ACTION_MODIFY = 7
    TRADE_RETCODE_DONE = 10009
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TIME_GTC = 0
    def __init__(self):
        self.requests = []
    def positions_get(self, **kwargs):
        return []
    def orders_get(self, **kwargs):
        return [FakeOrder()]
    def order_send(self, req):
        self.requests.append(req.copy())
        from types import SimpleNamespace
        return SimpleNamespace(retcode=10009, order=200)
    def symbol_info_tick(self, symbol):
        raise AssertionError('pending order modification must not look up live Bid/Ask')


class ActualBrokerRequest(unittest.TestCase):
    def test_pending_modification_request_contains_exact_prices(self):
        fake=FakeActualMT5()
        with (patch.object(E, 'TRADES', rows()),
              patch.object(E, 'HAVE_MT5', True),
              patch.object(E, 'DRY_RUN', False),
              patch.object(E, 'mt5', fake),
              patch.object(E, 'MAGIC', 190912),
              patch.object(E, 'mt5_ready', return_value=True),
              patch.object(E, 'broker_names', return_value=['MAIN']),
              patch.object(E, '_JR_LOADED', False)):
            result = E.mt5_edit_ticket(200, broker='MAIN', order_type='PENDING',
                                       entry=4050.99, sl=4000, tp=4055.99,
                                       expected_symbol='XAUUSDm', expected_direction='BUY')
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(fake.requests[0]['price'], 4050.99)
        self.assertEqual(fake.requests[0]['sl'], 4000)
        self.assertEqual(fake.requests[0]['tp'], 4055.99)
        self.assertEqual(fake.requests[0]['action'], 7)

    def test_broker_wrong_magic_blocked(self):
        fake=FakeActualMT5()
        with (patch.object(E, 'TRADES', rows()),
              patch.object(E, 'HAVE_MT5', True), patch.object(E, 'DRY_RUN', False),
              patch.object(E, 'mt5', fake), patch.object(E, 'MAGIC', 1234567),
              patch.object(E, 'mt5_ready', return_value=True),
              patch.object(E, 'broker_names', return_value=['MAIN']),
              patch.object(E, '_JR_LOADED', False)):
            result = E.mt5_edit_ticket(200, broker='MAIN', order_type='PENDING',
                                       entry=4050.99, sl=4000, tp=4055.99,
                                       expected_symbol='XAUUSDm', expected_direction='BUY')
        self.assertFalse(result['ok'])
        self.assertEqual(len(fake.requests), 0)
