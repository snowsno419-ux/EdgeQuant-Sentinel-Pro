"""Offline-only safety tests. No Telegram login or MT5 order_send occurs."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import edgequant_auto as E


class FakeMT5:
    """Mock terminal switching and identity validation, without order placement."""
    def __init__(self, main, second, *, wrong_login=False):
        self.main = main
        self.second = second
        self.active = None
        self.calls = []
        self.wrong_login = wrong_login

    def initialize(self, path=None, login=None, password=None, server=None):
        self.calls.append(('initialize', path, login, server))
        if path is None or str(path) == str(self.main / 'terminal64.exe'):
            self.active = ('MAIN', self.main)
            return True
        if str(path) == str(self.second / 'terminal64.exe'):
            self.active = ('EXNESS', self.second)
            return True
        return False

    def shutdown(self):
        self.active = None
        self.calls.append(('shutdown',))

    def terminal_info(self):
        if self.active is None:
            return None
        return SimpleNamespace(path=str(self.active[1]), connected=True, trade_allowed=True)

    def account_info(self):
        if self.active is None:
            return None
        if self.active[0] == 'MAIN':
            return SimpleNamespace(login=101, server='Main-Demo', balance=1000, currency='USD')
        return SimpleNamespace(login=999 if self.wrong_login else 202,
                               server='Exness-Demo', balance=1000, currency='USD')

    def last_error(self):
        return (0, 'ok')


class BrokerManagerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.main = self.root / 'main'
        self.extra = self.root / 'exness'
        for directory in (self.main, self.extra):
            directory.mkdir()
            (directory / 'terminal64.exe').write_bytes(b'fake')
        self.patches = [
            patch.object(E, '_user_brokers_folder', return_value=self.root),
            patch.object(E, '_broker_secure_storage_available', return_value=True),
            patch.object(E, 'MT5_ACCOUNTS', []),
            patch.object(E, 'HERE', self.root),
        ]
        for pa in self.patches:
            pa.start()
            self.addCleanup(pa.stop)
        # Stand-in for DPAPI in offline Linux tests (NOT used by the real application).
        self.patcher = patch.object(E, '_dpapi_crypt',
                side_effect=lambda data, protect: bytes(b ^ 0xA5 for b in data))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        E._MAIN_TERMINAL_EXE = ''
        E._MAIN_LOGIN = 0
        E._MAIN_SERVER = ''
        E.CURRENT_BROKER.update(name=None, ready=False)
        E.BROKERS_OFF = []
        E._BROKERS_OFF_TS = 0.0

    def add(self):
        return E.broker_save_account('EXNESS', 202, 'Exness-Demo', 'Secret-Goes-Here',
                                     str(self.extra / 'terminal64.exe'))

    def test_main_always_present_after_saving_extra(self):
        self.add()
        self.assertEqual([a['name'] for a in E.accounts()], ['MAIN', 'EXNESS'])
        self.assertFalse(E.broker_is_on('EXNESS'))
        self.assertTrue(E.broker_is_on('MAIN'))
        public = (self.root / 'edgequant_brokers.json').read_text()
        encrypted = (self.root / 'mt5_broker_passwords.dpapi').read_bytes()
        self.assertNotIn('Secret-Goes-Here', public)
        self.assertNotIn(b'Secret-Goes-Here', encrypted)
        self.assertEqual(E.accounts()[1]['password'], 'Secret-Goes-Here')

    def test_edit_without_password_preserves_existing_secret(self):
        self.add()
        E.broker_save_account('EXNESS', '202', 'Exness-Demo', '',
                              str(self.extra / 'terminal64.exe'))
        self.assertEqual(E.accounts()[1]['password'], 'Secret-Goes-Here')

    def test_invalid_path_rejected(self):
        with self.assertRaises(ValueError):
            E.broker_save_account('EXNESS', 202, 'Exness-Demo', '123',
                                   str(self.main / 'nonexistent-terminal64.exe'))
        self.assertEqual(len(E.accounts()), 1)

    def test_secret_must_be_protectable(self):
        with patch.object(E, '_dpapi_crypt', side_effect=RuntimeError('DPAPI unavailable')):
            with self.assertRaises(RuntimeError):
                self.add()
        self.assertFalse((self.root / 'edgequant_brokers.json').exists())

    def test_switch_main_extra_main_and_verify_identity(self):
        self.add()
        mock = FakeMT5(self.main, self.extra)
        with patch.object(E, 'mt5', mock), patch.object(E, 'HAVE_MT5', True):
            self.assertTrue(E.select_broker('MAIN'))
            self.assertEqual(E._MAIN_LOGIN, 101)
            self.assertTrue(E.select_broker('EXNESS'))
            self.assertEqual(E.CURRENT_BROKER['name'], 'EXNESS')
            self.assertTrue(E.select_broker('MAIN'))
            self.assertEqual(mock.active[0], 'MAIN')
            self.assertEqual(E.CURRENT_BROKER['name'], 'MAIN')
            self.assertEqual(len([x for x in mock.calls if x[0]=='initialize']), 3)

    def test_wrong_login_never_accepted(self):
        self.add()
        mock = FakeMT5(self.main, self.extra, wrong_login=True)
        with patch.object(E, 'mt5', mock), patch.object(E, 'HAVE_MT5', True):
            self.assertTrue(E.select_broker('MAIN'))
            self.assertFalse(E.select_broker('EXNESS'))
            self.assertIsNone(E.CURRENT_BROKER['name'])
            self.assertTrue(E.select_broker('MAIN'))
            self.assertEqual(mock.active[0], 'MAIN')

    def test_extra_terminal_cannot_be_main_terminal(self):
        self.add()
        mock = FakeMT5(self.main, self.extra)
        with patch.object(E, 'mt5', mock), patch.object(E, 'HAVE_MT5', True):
            self.assertTrue(E.select_broker('MAIN'))
            bad = E.accounts()
            bad[1]['path'] = str(self.main / 'terminal64.exe')
            with patch.object(E, 'accounts', return_value=bad):
                self.assertFalse(E.select_broker('EXNESS'))

    def test_main_cannot_be_removed_and_extra_removes_without_trading(self):
        self.add()
        self.assertFalse(E.broker_remove_account('MAIN'))
        self.assertTrue(E.broker_remove_account('EXNESS'))
        self.assertEqual([a['name'] for a in E.accounts()], ['MAIN'])
        self.assertNotIn('EXNESS', E._broker_secrets_read())

    def test_fallback_is_off_and_explicit_enable_adds_extra(self):
        self.add()
        self.assertFalse(E.BROKER_FALLBACK)
        self.assertEqual(E.broker_for_signal('GOLD LIMIT VIP'), ['MAIN'])
        E.set_broker_on('EXNESS', True, quiet=True)
        self.assertEqual(E.broker_for_signal('GOLD LIMIT VIP'), ['MAIN', 'EXNESS'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
