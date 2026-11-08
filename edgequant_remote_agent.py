#!/usr/bin/env python3
"""EdgeQuant outbound remote agent, protocol v1.

This first implementation can pair, poll, and verify signed commands. It is
intentionally READ-ONLY: every command is rejected because there is not yet a
reviewed/tested MT5 dispatcher. It never opens an inbound port and never calls
MetaTrader5 or changes Telegram/engine state.

Environment (publishable values are public; device token remains DPAPI-sealed):
  EDGEQUANT_SUPABASE_URL
  EDGEQUANT_SUPABASE_PUBLISHABLE_KEY
  EDGEQUANT_COMMAND_SIGNING_PUBLIC_KEY_B64
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

DEFAULT_SUPABASE_URL = "https://ybfltbhojvsbduntsqes.supabase.co"
# Publishable browser/app key only. Never replace this with a secret/service-role key.
DEFAULT_PUBLISHABLE_KEY = "sb_publishable_T8v4B3dRt_Pxf-Ho9-mqKQ_Q9wsHCs8"
SECRET_RE = re.compile(r"^[A-Za-z0-9_-]{43,64}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)
ALLOWED_COMMANDS = {
    "manual_market_order", "manual_pending_order", "modify_trade",
    "cancel_pending_order", "close_trade", "set_channel_enabled",
    "update_target_settings", "request_report", "refresh_snapshot",
}


def _b64url_decode(value: str) -> bytes:
    raw = value.replace("-", "+").replace("_", "/")
    return base64.b64decode(raw + "=" * ((4 - len(raw) % 4) % 4), validate=True)


def verify_signed_envelope(response: dict[str, Any], public_key_b64: str,
                           expected_device_id: str) -> dict[str, Any]:
    """Verify the exact signed UTF-8 bytes before trusting/parsing the command."""
    if not isinstance(response, dict) or response.get("status") != "claimed":
        raise ValueError("Relay response is not a claimed command")
    content, signature_text = response.get("signed_content"), response.get("signature")
    if not isinstance(content, str) or len(content.encode("utf-8")) > 16_384:
        raise ValueError("Signed command body is missing or too large")
    if not isinstance(signature_text, str):
        raise ValueError("Command signature is missing")
    public_bytes = _b64url_decode(public_key_b64)
    if len(public_bytes) != 32:
        raise ValueError("Ed25519 public key must be 32 bytes")
    signature = _b64url_decode(signature_text)
    try:
        Ed25519PublicKey.from_public_bytes(public_bytes).verify(signature, content.encode("utf-8"))
    except InvalidSignature as exc:
        raise ValueError("Command signature verification failed") from exc
    try:
        envelope = json.loads(content)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Signed command is not valid JSON") from exc
    if not isinstance(envelope, dict) or envelope.get("protocol_version") != 1:
        raise ValueError("Unsupported signed-command protocol")
    if envelope.get("device_id") != expected_device_id:
        raise ValueError("Signed command is for another device")
    if not UUID_RE.fullmatch(str(envelope.get("id", ""))):
        raise ValueError("Command id is invalid")
    if not UUID_RE.fullmatch(str(envelope.get("idempotency_key", ""))):
        raise ValueError("Command idempotency key is invalid")
    expiry_text = envelope.get("expires_at")
    if not isinstance(expiry_text, str):
        raise ValueError("Command expiry is missing")
    try:
        expiry = datetime.fromisoformat(expiry_text.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("Command expiry is invalid") from exc
    if expiry.timestamp() <= time.time():
        raise ValueError("Signed command has expired")
    if envelope.get("command_type") not in ALLOWED_COMMANDS:
        raise ValueError("Command type is not allowed by this agent build")
    if not isinstance(envelope.get("payload"), dict):
        raise ValueError("Command payload is invalid")
    return envelope


def validate_command_payload(command: dict[str, Any]) -> bool:
    """Basic defense-in-depth schema check. Local MT5-specific checks are still required."""
    kind = command.get("command_type")
    p = command.get("payload")
    if kind not in ALLOWED_COMMANDS or not isinstance(p, dict):
        return False
    if kind == "manual_market_order":
        keys = {"symbol", "direction", "volume", "stop_loss", "take_profit"}
        return (set(p) <= keys and {"symbol", "direction", "volume", "stop_loss", "take_profit"} <= set(p)
                and isinstance(p["symbol"], str) and bool(re.fullmatch(r"[A-Za-z0-9._-]{1,32}", p["symbol"]))
                and str(p["direction"]).upper() in ("BUY", "SELL")
                and _positive(p["volume"]) and _positive(p["stop_loss"]) and _positive(p["take_profit"]))
    if kind == "manual_pending_order":
        keys = {"symbol", "direction", "order_type", "volume", "entry", "stop_loss", "take_profit"}
        return (set(p) <= keys and keys <= set(p) and isinstance(p["symbol"], str)
                and bool(re.fullmatch(r"[A-Za-z0-9._-]{1,32}", p["symbol"]))
                and str(p["direction"]).upper() in ("BUY", "SELL")
                and str(p["order_type"]).upper() in ("BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP")
                and all(_positive(p[x]) for x in ("volume", "entry", "stop_loss", "take_profit")))
    if kind == "modify_trade":
        return (set(p) <= {"ticket", "stop_loss", "take_profit"}
                and isinstance(p.get("ticket"), int) and p["ticket"] > 0
                and (p.get("stop_loss") is None or _positive(p["stop_loss"]))
                and (p.get("take_profit") is None or _positive(p["take_profit"]))
                and (p.get("stop_loss") is not None or p.get("take_profit") is not None))
    if kind in ("cancel_pending_order", "close_trade"):
        return set(p) == {"ticket"} and isinstance(p.get("ticket"), int) and p["ticket"] > 0
    if kind == "set_channel_enabled":
        return (set(p) == {"channel_id", "enabled"} and isinstance(p.get("channel_id"), str)
                and 0 < len(p["channel_id"]) <= 128 and isinstance(p.get("enabled"), bool))
    if kind == "update_target_settings":
        return (set(p) == {"mode", "target", "stop_after_target"}
                and p.get("mode") in ("amount", "percent") and _positive(p.get("target"))
                and isinstance(p.get("stop_after_target"), bool))
    return kind in ("request_report", "refresh_snapshot") and not p


def _positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value < 1e9


def relay_url() -> str:
    project = os.environ.get("EDGEQUANT_SUPABASE_URL", DEFAULT_SUPABASE_URL).rstrip("/")
    if not project.startswith("https://"):
        raise RuntimeError("Supabase relay must use HTTPS")
    return project + "/functions/v1/edgequant-relay"


def publishable_key() -> str:
    key = os.environ.get("EDGEQUANT_SUPABASE_PUBLISHABLE_KEY", DEFAULT_PUBLISHABLE_KEY)
    if not key.startswith("sb_publishable_") and not key.startswith("eyJ"):
        raise RuntimeError("Set the Supabase publishable/anon key; never use a secret key here")
    return key


def relay_request(action: str, body: dict[str, Any] | None = None,
                  *, device_token: str | None = None, timeout: int = 12) -> dict[str, Any]:
    headers = {"apikey": publishable_key(), "content-type": "application/json", "accept": "application/json"}
    if device_token:
        headers["x-edgequant-device-token"] = device_token
    payload = {"action": action, **(body or {})}
    # requests verifies TLS by default; do not add verify=False.
    response = requests.post(relay_url(), json=payload, headers=headers, timeout=timeout)
    try:
        data = response.json()
    except ValueError:
        data = {"error": "Relay returned a non-JSON response"}
    if not response.ok:
        raise RuntimeError(str(data.get("error") or f"Relay request failed ({response.status_code})"))
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected relay response")
    return data


def _dpapi_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not available; DPAPI storage requires Windows")
    return Path(appdata) / "EdgeQuant" / "remote_agent.dpapi"


def _seal(data: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("Device credentials are sealed with Windows DPAPI; pair on the Windows PC")
    try:
        import win32crypt  # provided by pywin32
    except ImportError as exc:
        raise RuntimeError("Install pywin32 first: pip install pywin32") from exc
    protected = win32crypt.CryptProtectData(data, "EdgeQuant remote agent", None, None, None, 0)
    return protected[1] if isinstance(protected, tuple) else protected


def _unseal(data: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("Device credentials can only be unsealed on the paired Windows account")
    try:
        import win32crypt
    except ImportError as exc:
        raise RuntimeError("Install pywin32 first: pip install pywin32") from exc
    result = win32crypt.CryptUnprotectData(data, None, None, None, 0)
    return result[1]


def save_config(config: dict[str, Any]) -> Path:
    path = _dpapi_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    encrypted = _seal(json.dumps(config, separators=(",", ":")).encode("utf-8"))
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(encrypted)
    os.replace(temp, path)
    return path


def load_config() -> dict[str, Any]:
    path = _dpapi_path()
    if not path.exists():
        raise RuntimeError("No paired-device config found. Run --pair first on this Windows PC.")
    data = json.loads(_unseal(path.read_bytes()).decode("utf-8"))
    if not isinstance(data, dict) or not data.get("device_id") or not data.get("device_token"):
        raise RuntimeError("Paired-device config is invalid")
    return data


def pair_device(label: str) -> None:
    pair_code = secrets.token_urlsafe(32)
    device_token = secrets.token_urlsafe(32)
    if not SECRET_RE.fullmatch(pair_code) or not SECRET_RE.fullmatch(device_token):
        raise RuntimeError("Local secure random generator returned an unexpected token")
    print("Starting a 5-minute pairing request…")
    started = relay_request("pairing.start", {"pair_code": pair_code, "device_token": device_token, "label": label})
    print("Pairing requested. In the signed-in web app, open Connection & Pairing and enter this one-time code:")
    print("\n" + pair_code + "\n")
    print("Do not post or send the code publicly. Waiting for approval…")
    deadline = time.time() + 300
    while time.time() < deadline:
        state = relay_request("pairing.status", {"pair_code": pair_code})
        if state.get("status") == "claimed" and UUID_RE.fullmatch(str(state.get("device_id", ""))):
            config = {
                "supabase_url": os.environ.get("EDGEQUANT_SUPABASE_URL", DEFAULT_SUPABASE_URL),
                "publishable_key": publishable_key(),
                "device_id": state["device_id"],
                "device_token": device_token,
                "command_signing_public_key_b64": os.environ.get("EDGEQUANT_COMMAND_SIGNING_PUBLIC_KEY_B64", ""),
                "paired_at": datetime.now(timezone.utc).isoformat(),
            }
            path = save_config(config)
            print(f"Paired. The credential is DPAPI-encrypted for this Windows user: {path}")
            print("Command execution is not implemented in this build; the agent remains read-only.")
            return
        if state.get("status") in ("expired", "cancelled", "not_found"):
            raise RuntimeError("Pairing expired or was cancelled; start again")
        time.sleep(2)
    raise TimeoutError("Pairing code expired after 5 minutes; run --pair again")


def execute_command_read_only(command: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
    """Fail closed: no MT5 handler is included or invoked in this phase."""
    if not validate_command_payload(command):
        return "rejected", {"code": "invalid_or_unsupported_command"}, "invalid_command"
    return "rejected", {"code": "local_mt5_handler_not_installed"}, "remote_execution_disabled"


def command_signing_public_key(config: dict[str, Any]) -> str:
    """Use the DPAPI value, or permit secure post-pair env configuration."""
    return str(config.get("command_signing_public_key_b64") or
               os.environ.get("EDGEQUANT_COMMAND_SIGNING_PUBLIC_KEY_B64", ""))


def poll_once(config: dict[str, Any]) -> str:
    token = str(config.get("device_token", ""))
    device_id = str(config.get("device_id", ""))
    public_key = command_signing_public_key(config)
    if not SECRET_RE.fullmatch(token) or not UUID_RE.fullmatch(device_id):
        raise RuntimeError("Local device credentials are invalid")
    if not public_key:
        raise RuntimeError("Set EDGEQUANT_COMMAND_SIGNING_PUBLIC_KEY_B64 before polling commands")
    response = relay_request("agent.poll", {"device_id": device_id}, device_token=token)
    if response.get("status") == "idle":
        return "idle"
    try:
        command = verify_signed_envelope(response, public_key, device_id)
    except Exception as exc:
        # Do not execute or report an unverified command. The server will mark
        # the claimed command uncertain after its lease expires.
        print(f"Rejected unverified relay response: {exc}", file=sys.stderr)
        return "invalid_signature"
    outcome, result, error_code = execute_command_read_only(command)
    result_body = relay_request("agent.result", {
        "device_id": device_id,
        "command_id": command["id"],
        "outcome": outcome,
        "result": result,
        "error_code": error_code,
    }, device_token=token)
    print(f"Remote command {command['id']} safely rejected: {result_body.get('status', outcome)}")
    return str(result_body.get("status", outcome))


def selftest() -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    def enc(v: bytes) -> str:
        return base64.urlsafe_b64encode(v).decode().rstrip("=")
    command = {
        "protocol_version": 1,
        "id": "d4a274f0-624c-4da7-b659-495b1f173712",
        "device_id": "ecf133b8-1ec4-4bab-a6cf-c96c77fe7615",
        "idempotency_key": "cae547e8-c943-48da-a466-181a57101e68",
        "command_type": "manual_market_order",
        "payload": {"symbol": "EURUSD", "direction": "BUY", "volume": 0.01,
                    "stop_loss": 1.0, "take_profit": 1.1},
        "expires_at": "2999-01-01T00:00:00+00:00",
    }
    # The relay signs a stable JSON string. This test uses one exact byte string.
    content = json.dumps(command, separators=(",", ":"), sort_keys=True)
    signature = private.sign(content.encode())
    verified = verify_signed_envelope({"status": "claimed", "signed_content": content,
                                       "signature": enc(signature)}, enc(public), command["device_id"])
    assert verified["id"] == command["id"]
    assert validate_command_payload(verified)
    try:
        verify_signed_envelope({"status": "claimed", "signed_content": content + " ",
                                "signature": enc(signature)}, enc(public), command["device_id"])
    except ValueError:
        pass
    else:
        raise AssertionError("Tampered signature was accepted")
    print("EdgeQuant remote agent self-test passed (signature verification + fail-closed command validation).")


def main() -> int:
    parser = argparse.ArgumentParser(description="EdgeQuant outbound relay agent (read-only / no MT5 execution)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pair", action="store_true", help="Start one-time pairing on this Windows PC")
    group.add_argument("--poll", action="store_true", help="Poll the relay; commands are safely rejected")
    group.add_argument("--selftest", action="store_true", help="Run offline protocol checks")
    parser.add_argument("--label", default="EdgeQuant Windows PC")
    parser.add_argument("--once", action="store_true", help="Poll only once instead of looping")
    parser.add_argument("--interval", type=float, default=5.0, help="Poll interval (seconds; min 3)")
    args = parser.parse_args()
    try:
        if args.selftest:
            selftest()
        elif args.pair:
            pair_device(args.label)
        else:
            config = load_config()
            interval = max(3.0, min(60.0, args.interval))
            while True:
                try:
                    state = poll_once(config)
                    if state not in ("idle", "succeeded", "rejected"):
                        print("Relay state:", state)
                except Exception as exc:
                    print("Relay poll error:", str(exc), file=sys.stderr)
                if args.once:
                    break
                time.sleep(interval)
        return 0
    except KeyboardInterrupt:
        print("Remote agent stopped.")
        return 130
    except Exception as exc:
        print("Remote agent:", str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
