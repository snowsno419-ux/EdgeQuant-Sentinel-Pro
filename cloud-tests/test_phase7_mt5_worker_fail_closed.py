"""Offline tests for signed DEMO worker safety. No MetaTrader5 installation/credentials needed."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

class FakeMT5(types.ModuleType):
    ACCOUNT_TRADE_MODE_DEMO = 0
    def __init__(self):
        super().__init__('MetaTrader5')
        self.connected=True
        self.stopped=0
        self.positions=()
        self.orders=()
    def initialize(self, path=None): return True
    def account_info(self):
        return types.SimpleNamespace(trade_mode=0, login=52985798,
            server='ICMarketsSC-Demo', balance=100, equity=110, profit=10)
    def terminal_info(self): return types.SimpleNamespace(connected=self.connected)
    def positions_get(self): return self.positions
    def orders_get(self): return self.orders
    def shutdown(self): self.stopped+=1

class TestDemoReadOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake=FakeMT5()
        cls.previous=sys.modules.get('MetaTrader5')
        sys.modules['MetaTrader5']=cls.fake
        file=Path(__file__).resolve().parents[1]/'cloud-worker'/'edgequant_demo_worker.py'
        spec=importlib.util.spec_from_file_location('_eq_mt5_readonly_test',file)
        cls.worker=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.worker)
    @classmethod
    def tearDownClass(cls):
        if cls.previous is None: sys.modules.pop('MetaTrader5',None)
        else: sys.modules['MetaTrader5']=cls.previous
    def setUp(self):
        self.fake.connected=True
        self.fake.positions=()
        self.fake.orders=()
        self.fake.stopped=0
    def test_disconnected_terminal_rejected_and_closed(self):
        self.fake.connected=False
        with self.assertRaisesRegex(RuntimeError,'disconnected'):
            self.worker.mt5_account()
        self.assertEqual(self.fake.stopped,1)
    def test_failed_positions_query_must_never_send_fabricated_zero(self):
        self.fake.positions=None
        args=types.SimpleNamespace(broker_id='broker_1234567890',server='ICMarketsSC-Demo',
            login='52985798',terminal=None,once=True)
        private=Ed25519PrivateKey.generate()
        with patch.object(self.worker,'keys',return_value=('worker_1234567890',private)),patch.object(self.worker,'request') as send:
            self.worker.observe(args)
            send.assert_not_called()
        self.assertEqual(self.fake.stopped,1)
    def test_valid_signed_snapshot_has_exact_broker_identity(self):
        self.fake.positions=(1,2)
        self.fake.orders=(3,)
        args=types.SimpleNamespace(broker_id='broker_1234567890',server='ICMarketsSC-Demo',
            login='52985798',terminal=None,once=True)
        private=Ed25519PrivateKey.generate()
        with patch.object(self.worker,'keys',return_value=('worker_1234567890',private)),patch.object(self.worker,'request',return_value=(202,{'accepted':True})) as send:
            self.worker.observe(args)
            self.assertEqual(send.call_count,1)
            payload=send.call_args.args[1]
            self.assertEqual(payload['mode'],'DEMO')
            self.assertEqual(payload['login_hint'],'52985798')
            self.assertEqual(payload['open_positions'],2)
            self.assertEqual(payload['pending_orders'],1)
            self.assertTrue(payload['terminal_connected'])
        self.assertEqual(self.fake.stopped,1)

if __name__=='__main__': unittest.main()
