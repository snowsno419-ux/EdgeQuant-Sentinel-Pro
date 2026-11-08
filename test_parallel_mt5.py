"""Offline-only checks for parallel fan-out. Never logs into a real MT5 terminal."""
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import edgequant_auto as E
import edgequant_parallel_mt5 as P


class ParallelBrokerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_all_workers_launch_concurrently_not_sequentially(self):
        barrier = threading.Barrier(2, timeout=3)
        names = []
        lock = threading.Lock()

        def fake_runner(command, **kw):
            job = json.loads(kw['input'])
            with lock:
                names.append(job['broker'])
            barrier.wait()
            result = {'broker': job['broker'], 'status': 'placed', 'tickets': [99]}
            return SimpleNamespace(returncode=0, stdout=P.RESULT_PREFIX + json.dumps(result), stderr='')

        jobs = [{'broker': 'MAIN'}, {'broker': 'EXNESS'}]
        output = P.dispatch_all(self.root / 'edgequant_auto.py', jobs, runner=fake_runner)
        self.assertEqual({x['broker'] for x in output}, {'MAIN', 'EXNESS'})
        self.assertEqual({x['status'] for x in output}, {'placed'})
        self.assertEqual(set(names), {'MAIN', 'EXNESS'})

    def test_missing_worker_receipt_is_uncertain_not_auto_retry(self):
        def runner(command, **kwargs):
            return SimpleNamespace(returncode=1, stdout='worker crash', stderr='secret')
        row = P._run_one(self.root / 'edgequant_auto.py', {'broker': 'MAIN'}, runner=runner)
        self.assertEqual(row['status'], 'uncertain')
        self.assertIn('no retry', row['error'])
        self.assertNotIn('secret', str(row))

    def test_timeout_is_uncertain_not_automatically_resubmitted(self):
        import subprocess
        def runner(*a, **k):
            raise subprocess.TimeoutExpired(a[0], 1)
        row = P._run_one(self.root / 'edgequant_auto.py', {'broker': 'EXNESS'}, runner=runner)
        self.assertEqual(row['status'], 'uncertain')
        self.assertIn('no retry', row['error'])

    def test_account_scoped_atomic_dedup_claim(self):
        with patch.object(E, '_user_brokers_folder', return_value=self.root):
            self.assertTrue(E.parallel_worker_claim(-1005, 77, 'MAIN', 100, 'Main-Demo'))
            self.assertFalse(E.parallel_worker_claim(-1005, 77, 'MAIN', 100, 'Main-Demo'))
            self.assertTrue(E.parallel_worker_claim(-1005, 77, 'EXNESS', 200, 'Exness-Demo'))
            self.assertTrue(E.parallel_worker_claim(-1005, 78, 'MAIN', 100, 'Main-Demo'))
            files = list((self.root / 'parallel_mt5_claims').glob('*.json'))
            self.assertEqual(len(files), 3)
            self.assertFalse(E.parallel_worker_claim(0, 1, 'MAIN', 100, 'Main-Demo'))

    def test_dry_run_does_not_claim_live_signal_id(self):
        with patch.object(E, '_user_brokers_folder', return_value=self.root):
            self.assertTrue(E.parallel_worker_claim(-1005, 77, 'MAIN', 100, 'Main-Demo', dry_run=True))
            self.assertFalse((self.root / 'parallel_mt5_claims').exists())

    def test_worker_rejects_disconnected_or_unverified_broker(self):
        job = {'broker': 'MAIN', 'chat_id': -100, 'message_id': 4, 'signal': {'action': 'place'}}
        with patch.object(E, 'parallel_worker_connect', return_value=(False, 'wrong login', None)), \
             patch.object(E, 'edgequant_external_stop_active', return_value=False):
            row = E.parallel_worker_execute(job)
        self.assertEqual(row['status'], 'skipped')
        self.assertEqual(row['error'], 'wrong login')

    def test_worker_is_locked_to_single_broker_for_risk_guard(self):
        signal = E.Signal(action='place', direction='BUY', symbol='XAUUSD',
                          entries=[3901], sl=3895, tps=[3924], confidence='high')
        job = {'broker': 'EXNESS', 'chat_id': -1005, 'message_id': 701, 'source': 'GOLD LIMIT VIP',
               'category': 'LIMIT', 'signal': signal.to_dict(), 'signal_ts': time.time(),
               'dry_run': False}
        info = SimpleNamespace(login=200, server='Exness-Demo', balance=1000)
        mt5 = SimpleNamespace(symbol_info_tick=lambda sym: SimpleNamespace(ask=3910, bid=3909),
                              orders_get=lambda symbol=None: [],
                              positions_get=lambda symbol=None: [],
                              shutdown=lambda: None)
        sent = []
        def plan_orders(*args, **kw):
            return [{'kind': 'PENDING', 'type': 'BUY_LIMIT', 'price': 3901.99,
                     'src_price': 3901, 'direct_limit': True, 'layer': layer,
                     'sl': 3895, 'tp': 3906.99 if layer == 1 else 3924,
                     'tag': 'quick' if layer == 1 else 'signal', 'lot': 0.01}
                    for layer in (1, 2)]
        def send(plan, symbol, **kwargs):
            self.assertEqual(E.broker_names(), ['EXNESS'])
            sent.append((symbol, len(plan)))
            for layer, order in enumerate(plan, 1):
                order.update(status='pending', ticket=1233 + layer)
            return [1234, 1235]
        patches = [patch.object(E, '_user_brokers_folder', return_value=self.root),
                   patch.object(E, 'mt5', mt5), patch.object(E, 'HAVE_MT5', True),
                   patch.object(E, 'parallel_worker_connect', return_value=(True, '', info)),
                   patch.object(E, 'edgequant_external_stop_active', return_value=False),
                   patch.object(E, 'resolve_symbol', return_value='XAUUSDm'),
                   patch.object(E, 'can_trade_now', side_effect=lambda sym: (E.broker_names()==['EXNESS'], 'wrong broker')),
                   patch.object(E, 'extra_guards', return_value=(True, '')),
                   patch.object(E, 'stale_signal', return_value=(False, '')),
                   patch.object(E, 'broker_from_mt5', return_value=SimpleNamespace()),
                   patch.object(E, 'build_plan', side_effect=plan_orders),
                   patch.object(E, 'execute_plan', side_effect=send),
                   patch.object(E, 'DRY_RUN', False)]
        original_fn = E.broker_names
        try:
            for item in patches:
                item.start()
            row = E.parallel_worker_execute(job)
            self.assertEqual(row['status'], 'placed')
            self.assertEqual(row['tickets'], [1234, 1235])
            self.assertEqual(sent, [('XAUUSDm', 2)])
            # A NEW Telegram post ID with identical entry/SL/TP must not
            # submit another pair to the same verified MT5 account.
            second = dict(job, message_id=702)
            duplicate = E.parallel_worker_execute(second)
            self.assertEqual(duplicate['status'], 'duplicate')
            self.assertEqual(duplicate['tickets'], [])
            self.assertEqual(sent, [('XAUUSDm', 2)])
        finally:
            for item in reversed(patches):
                item.stop()
            E.broker_names = original_fn

    def test_parent_fans_out_and_journals_same_ticket_per_different_brokers(self):
        main = self.root / 'Main' / 'terminal64.exe'
        extra = self.root / 'Extra' / 'terminal64.exe'
        main.parent.mkdir()
        extra.parent.mkdir()
        main.touch()
        extra.touch()
        old_identity = (E._MAIN_TERMINAL_EXE, E._MAIN_LOGIN, E._MAIN_SERVER)
        E._MAIN_TERMINAL_EXE, E._MAIN_LOGIN, E._MAIN_SERVER = str(main), 101, 'Main-Demo'
        self.addCleanup(lambda: (setattr(E, '_MAIN_TERMINAL_EXE', old_identity[0]),
                                  setattr(E, '_MAIN_LOGIN', old_identity[1]),
                                  setattr(E, '_MAIN_SERVER', old_identity[2])))
        records = []
        dispatched = []
        def fake_dispatch(script, jobs):
            dispatched.extend(jobs)
            return [{'broker': job['broker'], 'status': 'placed', 'symbol': 'XAUUSDm',
                     'tickets': [98765], 'orders': [{'status': 'pending', 'ticket': 98765,
                     'kind': 'PENDING', 'type': 'BUY_LIMIT', 'price': 3901.99,
                     'sl': 3895, 'tp': 3924, 'lot': 0.01, 'tag': 'quick50'}]}
                    for job in jobs]
        sig = E.Signal(action='place', direction='BUY', symbol='XAUUSD',
                       entries=[3901], sl=3895, tps=[3924], confidence='high')
        sig.msg_ts = time.time()
        with patch.object(E, 'accounts', return_value=[{'name': 'MAIN'},
                  {'name': 'EXNESS', 'login': 202, 'server': 'Exness-Demo', 'path': str(extra)}]), \
             patch.object(E, 'broker_is_on', return_value=True), \
             patch.object(E, 'MAX_OPEN_ORDERS', 0), \
             patch.object(E, 'TRADE_JOURNAL', True), \
             patch.object(E, 'AUTO_BE_ENABLED', False), \
             patch.object(E, 'jr_place', side_effect=lambda *args, **kw: records.append(kw['broker'])), \
             patch.object(P, 'dispatch_all', side_effect=fake_dispatch):
            E.parallel_broker_signal(sig, 'LIMIT', 'GOLD LIMIT VIP', -1005, 701,
                                     'GOLD BUY 3901 SL 3895 TP 3924', ['MAIN', 'EXNESS'])
        self.assertEqual({x['broker'] for x in dispatched}, {'MAIN', 'EXNESS'})
        self.assertEqual(set(records), {'MAIN', 'EXNESS'})
        self.assertEqual(E.BROKER_TICKETS['MAIN'], {98765})
        self.assertEqual(E.BROKER_TICKETS['EXNESS'], {98765})
        self.assertTrue(all('password' not in str(x).lower() for x in dispatched))

    def test_duplicate_terminal_executable_blocks_entire_fanout(self):
        main = self.root / 'Main' / 'terminal64.exe'
        main.parent.mkdir()
        main.touch()
        original = (E._MAIN_TERMINAL_EXE, E._MAIN_LOGIN, E._MAIN_SERVER)
        E._MAIN_TERMINAL_EXE, E._MAIN_LOGIN, E._MAIN_SERVER = str(main), 101, 'Main-Demo'
        self.addCleanup(lambda: (setattr(E, '_MAIN_TERMINAL_EXE', original[0]),
                                  setattr(E, '_MAIN_LOGIN', original[1]),
                                  setattr(E, '_MAIN_SERVER', original[2])))
        sig = E.Signal(action='place', direction='BUY', symbol='XAUUSD', entries=[3901], sl=3895,
                       tps=[3924], confidence='high')
        audits = []
        with patch.object(E, 'accounts', return_value=[{'name': 'MAIN'},
                  {'name': 'EXNESS', 'login': 202, 'server': 'Exness-Demo', 'path': str(main)}]), \
             patch.object(E, 'broker_is_on', return_value=True), \
             patch.object(E, 'MAX_OPEN_ORDERS', 0), \
             patch.object(P, 'dispatch_all') as start:
            E.parallel_broker_signal(sig, 'LIMIT', 'GOLD LIMIT VIP', -1005, 701,
                                     'original post', ['MAIN', 'EXNESS'],
                                     audit=lambda *a, **k: audits.append(a))
        start.assert_not_called()
        self.assertTrue(any('blocked' in x for x in audits))

    def test_position_manager_isolates_same_ticket_number_across_accounts(self):
        import asyncio
        current = {'name': 'MAIN'}
        trails = []
        calls = [0]
        async def sleep_once(seconds):
            calls[0] += 1
            if calls[0] > 1:
                raise asyncio.CancelledError()
        def select(name):
            current['name'] = name
            E.CURRENT_BROKER['name'] = name
            return True
        def positions():
            return [SimpleNamespace(ticket=1234, symbol='XAUUSD', magic=E.MAGIC,
                                    type=0, sl=3890, price_open=3900)]
        def record_trail(pos):
            trails.append((current['name'], pos.ticket))
        previous = dict(E.CURRENT_BROKER)
        with patch.object(E, 'HAVE_MT5', True), \
             patch.object(E, 'DRY_RUN', False), \
             patch.object(E, 'mt5_ready', return_value=True), \
             patch.object(E, 'broker_names', return_value=['MAIN', 'EXNESS']), \
             patch.object(E, 'select_broker', side_effect=select), \
             patch.object(E, 'mt5', SimpleNamespace(positions_get=positions)), \
             patch.object(E.asyncio, 'sleep', side_effect=sleep_once), \
             patch.object(E, 'TRAILING_STOP', True), \
             patch.object(E, 'AUTO_BE_ENABLED', False), \
             patch.object(E, 'RUNNER_MODE', False), \
             patch.object(E, 'AGENT_ENABLED', False), \
             patch.object(E, 'PENDING_EXPIRY_HOURS', 0), \
             patch.object(E, 'PARTIAL_CLOSE_PIPS', 0), \
             patch.object(E, 'PARTIAL_LADDER', ''), \
             patch.object(E, 'GROUPS', [{'broker':'MAIN', 'tickets':[1234], 'be_on_tp1':False},
                                         {'broker':'EXNESS','tickets':[1234], 'be_on_tp1':False}]) as groups, \
             patch.object(E, 'trail_one', side_effect=record_trail):
            with self.assertRaises(asyncio.CancelledError):
                asyncio.run(E.manage_positions())
            self.assertEqual(len(groups), 2)
        E.CURRENT_BROKER.update(previous)
        self.assertEqual(trails, [('MAIN', 1234), ('EXNESS', 1234)])

    def test_parallel_worker_does_not_accept_unset_broker_credentials(self):
        main = self.root / 'MAIN' / 'terminal64.exe'
        main.parent.mkdir()
        main.write_bytes(b'fake')
        extra = self.root / 'EXNESS' / 'terminal64.exe'
        extra.parent.mkdir()
        extra.write_bytes(b'fake')
        job = {'broker': 'EXNESS', 'source': 'GOLD LIMIT VIP', 'chat_id': -100,
               'identity': {'path': str(extra), 'login': 22, 'server': 'Wrong-Server'},
               'main_path': str(main)}
        extra_account = {'name': 'EXNESS', 'path': str(extra), 'login': 22,
                         'server': 'Exness-Demo', 'password': 'TEST'}
        with patch.object(E, 'HAVE_MT5', True), \
             patch.object(E, 'mt5', SimpleNamespace()), \
             patch.object(E, 'accounts', return_value=[extra_account]), \
             patch.object(E, 'broker_for_signal', return_value=['MAIN', 'EXNESS']):
            ok, reason, _ = E.parallel_worker_connect(job)
            self.assertFalse(ok)
            self.assertIn('changed', reason)


if __name__ == '__main__':
    unittest.main()
