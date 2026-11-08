"""Offline tests for Telegram auto-reconnect policy; no Telegram/MT5/network use."""
import asyncio
import unittest
from unittest.mock import patch

import edgequant_auto as engine


class FakeTelegramClient:
    def __init__(self, failures=0, failure=None):
        self.failures = failures
        self.failure = failure or ConnectionError("network is unreachable")
        self.attempts = 0
        self.connected = False

    async def start(self):
        self.attempts += 1
        if self.attempts <= self.failures:
            self.connected = False
            raise self.failure
        self.connected = True
        return self

    def is_connected(self):
        return self.connected

    async def disconnect(self):
        self.connected = False


async def no_wait(_seconds):
    await asyncio.sleep(0)


class TelegramReconnectTests(unittest.TestCase):
    def test_saved_session_retries_transient_startup_outage_until_connected(self):
        client = FakeTelegramClient(failures=2)
        with patch.object(engine, "tg_session_exists", return_value=True), \
             patch.object(engine, "tg_status_write"), \
             patch.object(engine, "tg_set_state"), \
             patch.object(engine, "log"), \
             patch.object(engine, "STOP_REQUESTED", False):
            result = asyncio.run(engine.tg_login_with_timeout(
                client, timeout=0.1, _sleep_fn=no_wait))
        self.assertTrue(result)
        self.assertEqual(client.attempts, 3)
        self.assertTrue(client.is_connected())

    def test_no_saved_session_does_not_retry_a_connection_error(self):
        client = FakeTelegramClient(failures=10)
        with patch.object(engine, "tg_session_exists", return_value=False), \
             patch.object(engine, "tg_status_write"), \
             patch.object(engine, "tg_set_state"), \
             patch.object(engine, "log"), \
             patch.object(engine, "STOP_REQUESTED", False):
            result = asyncio.run(engine.tg_login_with_timeout(
                client, timeout=0.1, _sleep_fn=no_wait))
        self.assertFalse(result)
        self.assertEqual(client.attempts, 1)

    def test_permanent_authorization_error_is_not_retried_as_network(self):
        client = FakeTelegramClient(
            failures=10,
            failure=RuntimeError("AUTH_KEY_UNREGISTERED: The key is not registered"))
        with patch.object(engine, "tg_session_exists", return_value=True), \
             patch.object(engine, "tg_status_write"), \
             patch.object(engine, "tg_set_state"), \
             patch.object(engine, "log"), \
             patch.object(engine, "STOP_REQUESTED", False):
            result = asyncio.run(engine.tg_login_with_timeout(
                client, timeout=0.1, _sleep_fn=no_wait))
        self.assertFalse(result)
        self.assertEqual(client.attempts, 1)
        self.assertIsInstance(engine._LAST_LOGIN_EXC, RuntimeError)

    def test_transient_classifier_excludes_revoked_authorizations(self):
        self.assertTrue(engine.telegram_transient_connection_error(
            ConnectionError("connection reset by peer")))
        self.assertFalse(engine.telegram_transient_connection_error(
            RuntimeError("AUTH_KEY_UNREGISTERED: The key is not registered")))
        self.assertFalse(engine.telegram_transient_connection_error(
            ValueError("invalid API hash")))


if __name__ == "__main__":
    unittest.main()
