"""Offline, no-network tests for EdgeQuant Telegram-login code request flow.
Run: python test_telegram_code_guard.py (with edgequant_auto.py alongside)."""
import asyncio
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
import edgequant_auto as E


class SendCodeUnavailableError(Exception):
    pass


class FakeTelegramClient:
    instances = []
    should_fail = False
    authorized = False
    def __init__(self, *args, **kwargs):
        self.connect_count = 0
        self.sent = []
        self.used = []
        self.closed = False
        self.is_auth = type(self).authorized
        type(self).instances.append(self)
    def is_connected(self):
        return self.connect_count > 0 and not self.closed
    async def connect(self):
        self.connect_count += 1
        self.closed = False
    async def disconnect(self):
        self.closed = True
    async def is_user_authorized(self):
        return self.is_auth
    async def send_code_request(self, phone):
        self.sent.append(phone)
        if type(self).should_fail:
            raise SendCodeUnavailableError("all available code methods were used (ResendCodeRequest)")
        return SimpleNamespace(phone_code_hash="test-hash")
    async def sign_in(self, *args, **kwargs):
        self.used.append(kwargs)
        self.is_auth = True
    async def get_me(self):
        return SimpleNamespace(first_name="OfflineTest", last_name="", username="tester")


class TelegramCodeGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = {k:getattr(E,k) for k in (
            "HERE","TelegramClient","API_ID","API_HASH","_login_client",
            "_login_pending_phone","_login_pending_at","_login_send_block_until",
            "TG_STATE", "tg_status_write", "telegram_credentials_ready")}
        E.HERE = Path(self.tmp.name)
        E.TelegramClient = FakeTelegramClient
        E.API_ID = 12345678
        E.API_HASH = "a"*32
        E.telegram_credentials_ready = lambda: True
        E._login_client = None
        E._login_pending_phone = ""
        E._login_pending_at = 0
        E._login_send_block_until = 0
        E.TG_STATE = {"online":False,"phase":"idle","reason":"","who":"", "ts":0}
        E.tg_status_write = lambda *a,**kw: None
        FakeTelegramClient.instances = []
        FakeTelegramClient.should_fail = False
        FakeTelegramClient.authorized = False
    def tearDown(self):
        for k,v in self.old.items():
            setattr(E,k,v)
        self.tmp.cleanup()
    def run_async(self,coro):
        return asyncio.run(coro)
    def test_second_click_reuses_code_not_resend(self):
        x=self.run_async(E.tg_login_send_code('+10000000000'))
        y=self.run_async(E.tg_login_send_code('+10000000000'))
        self.assertTrue(x['ok'])
        self.assertTrue(y['already_sent'])
        self.assertEqual(len(FakeTelegramClient.instances),1)
        self.assertEqual(FakeTelegramClient.instances[0].sent,['+10000000000'])
        self.assertTrue(E.tg_login_code_pending('+10000000000'))
    def test_different_phone_while_pending_not_sent(self):
        self.run_async(E.tg_login_send_code('+10000000000'))
        x=self.run_async(E.tg_login_send_code('+20000000000'))
        self.assertFalse(x['ok'])
        self.assertEqual(FakeTelegramClient.instances[0].sent,['+10000000000'])
    def test_wrong_phone_code_not_signed_in(self):
        self.run_async(E.tg_login_send_code('+10000000000'))
        x=self.run_async(E.tg_login_enter_code('+20000000000','12345'))
        self.assertFalse(x['ok'])
        self.assertEqual(FakeTelegramClient.instances[0].used, [])
    def test_code_is_used_successfully_and_pending_cleared(self):
        self.run_async(E.tg_login_send_code('+10000000000'))
        x=self.run_async(E.tg_login_enter_code('+10000000000','12345'))
        self.assertTrue(x['ok'])
        self.assertFalse(E.tg_login_code_pending())
        self.assertIsNone(E._login_client)
        self.assertTrue(FakeTelegramClient.instances[0].closed)
    def test_existing_valid_session_skips_new_code(self):
        FakeTelegramClient.authorized = True
        x=self.run_async(E.tg_login_send_code('+10000000000'))
        self.assertTrue(x['ok'])
        self.assertIn('who',x)
        self.assertEqual(FakeTelegramClient.instances[0].sent, [])
    def test_unavailable_is_friendly_and_locally_throttled(self):
        FakeTelegramClient.should_fail = True
        x=self.run_async(E.tg_login_send_code('+10000000000'))
        self.assertFalse(x['ok'])
        self.assertIn('SEND_CODE_UNAVAILABLE',x['error'])
        self.assertIsNone(E._login_client)
        self.assertEqual(len(FakeTelegramClient.instances),1)
        again=self.run_async(E.tg_login_send_code('+10000000000'))
        self.assertFalse(again['ok'])
        self.assertIn('retry pause',again['error'])
        self.assertEqual(len(FakeTelegramClient.instances),1)
        self.assertTrue((E.HERE/E.LOGIN_CODE_RETRY_FILE).exists())
    def test_cooldown_persists_across_local_client_restart(self):
        E._tg_login_set_retry_until(900)
        E._login_send_block_until = 0
        x=self.run_async(E.tg_login_send_code('+10000000000'))
        self.assertFalse(x['ok'])
        self.assertEqual(len(FakeTelegramClient.instances),0)
    def test_expired_pending_new_client_instead_of_implicit_resend(self):
        self.run_async(E.tg_login_send_code('+10000000000'))
        E._login_pending_at = time.time() - E.LOGIN_CODE_PENDING_SECONDS - 1
        x=self.run_async(E.tg_login_send_code('+10000000000'))
        self.assertTrue(x['ok'])
        self.assertEqual(len(FakeTelegramClient.instances),2)
        self.assertTrue(FakeTelegramClient.instances[0].closed)
        self.assertEqual(FakeTelegramClient.instances[1].sent,['+10000000000'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
