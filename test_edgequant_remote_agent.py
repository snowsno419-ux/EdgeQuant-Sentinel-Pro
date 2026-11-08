from __future__ import annotations
import base64
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import edgequant_remote_agent as agent


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


class RemoteAgentProtocolTests(unittest.TestCase):
    def setUp(self):
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        self.device_id = "ecf133b8-1ec4-4bab-a6cf-c96c77fe7615"
        self.command = {
            "protocol_version": 1,
            "id": "d4a274f0-624c-4da7-b659-495b1f173712",
            "device_id": self.device_id,
            "idempotency_key": "cae547e8-c943-48da-a466-181a57101e68",
            "command_type": "manual_market_order",
            "payload": {
                "symbol": "EURUSD", "direction": "BUY", "volume": 0.01,
                "stop_loss": 1.0, "take_profit": 1.1,
            },
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
        }
        self.content = json.dumps(self.command, separators=(",", ":"), sort_keys=True)
        self.response = {
            "status": "claimed",
            "signed_content": self.content,
            "signature": b64url(self.private.sign(self.content.encode("utf-8"))),
        }

    def test_valid_ed25519_envelope_verifies(self):
        parsed = agent.verify_signed_envelope(self.response, b64url(self.public), self.device_id)
        self.assertEqual(parsed["id"], self.command["id"])
        self.assertTrue(agent.validate_command_payload(parsed))

    def test_tampering_fails_signature(self):
        tampered = dict(self.response)
        tampered["signed_content"] += " "
        with self.assertRaisesRegex(ValueError, "signature verification failed"):
            agent.verify_signed_envelope(tampered, b64url(self.public), self.device_id)

    def test_wrong_device_rejected(self):
        with self.assertRaisesRegex(ValueError, "another device"):
            agent.verify_signed_envelope(self.response, b64url(self.public), "9cf133b8-1ec4-4bab-a6cf-c96c77fe7615")

    def test_expired_command_rejected(self):
        self.command["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        self.content = json.dumps(self.command, separators=(",", ":"), sort_keys=True)
        self.response = {"status": "claimed", "signed_content": self.content,
                         "signature": b64url(self.private.sign(self.content.encode()))}
        with self.assertRaisesRegex(ValueError, "expired"):
            agent.verify_signed_envelope(self.response, b64url(self.public), self.device_id)

    def test_missing_stop_loss_fails_closed(self):
        self.command["payload"].pop("stop_loss")
        self.assertFalse(agent.validate_command_payload(self.command))

    def test_signing_key_can_be_added_after_pairing(self):
        key = b64url(self.public)
        with patch.dict(agent.os.environ, {"EDGEQUANT_COMMAND_SIGNING_PUBLIC_KEY_B64": key}):
            self.assertEqual(agent.command_signing_public_key({}), key)
            self.assertEqual(agent.command_signing_public_key({"command_signing_public_key_b64": "stored"}), "stored")

    def test_dispatcher_never_executes_orders(self):
        status, result, code = agent.execute_command_read_only(self.command)
        self.assertEqual(status, "rejected")
        self.assertEqual(code, "remote_execution_disabled")
        self.assertEqual(result["code"], "local_mt5_handler_not_installed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
