"""
EdgeQuant Sentinel Pro — Personal Telegram private cloud listener (READ-ONLY).

Run one isolated worker process per consenting account on a hardened, always-on
Python host. Requires Telethon and cryptography. Never calls Telegram send_message
or forwards any credentials to Vercel/Neon. Does NOT place MT5 orders.

This is a headless PRIVATE-HOST operator CLI for initial testing; it is NOT a
mobile browser OTP flow. Never type a phone code into ChatGPT.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time
import urllib.error
import urllib.request

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from telethon import TelegramClient, events
    from telethon.errors import SessionPasswordNeededError
    from telethon.sessions import StringSession
    from telethon.tl.types import Channel, Chat
except ImportError as exc:
    raise SystemExit("Install privately: python -m pip install telethon cryptography") from exc

API_ORIGIN = "https://edgequant-mobile-web.vercel.app"
CHAT_RE = re.compile(r"^-?[0-9]{5,20}$")
DATA_DIR = Path(os.environ.get("EQ_PRIVATE_DATA_DIR", str(Path.home() / ".edgequant_personal_telegram")))
SESS_PATH = DATA_DIR / "telegram_session.enc"
IDENTITY_PATH = DATA_DIR / "worker_identity.enc"
SYNC_INTERVAL = 120


def env_settings() -> tuple[int, str, Fernet]:
    try:
        api_id = int(os.environ.get("EQ_TG_API_ID", "0"))
        api_hash = os.environ["EQ_TG_API_HASH"]
        key = os.environ["EQ_TG_ENCRYPTION_KEY"]
        if api_id <= 0 or not re.fullmatch(r"[a-f0-9]{32}", api_hash):
            raise ValueError("Invalid private Telegram developer application credentials")
        return api_id, api_hash, Fernet(key.encode("ascii"))
    except (KeyError, ValueError) as exc:
        raise RuntimeError("Worker missing valid private Telegram API credentials or encryption key") from exc


def init_storage() -> None:
    DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    if DATA_DIR.is_symlink():
        raise RuntimeError("Refusing symlinked private storage directory")
    if os.name != "nt" and (DATA_DIR.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO)):
        raise RuntimeError("Worker storage directory must not be accessible by other users")


def write_encrypted(path: Path, content: bytes, fernet: Fernet) -> None:
    init_storage()
    if path.exists():
        raise RuntimeError("Refusing to overwrite an existing encrypted worker secret")
    token = fernet.encrypt(content)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(token)


def read_encrypted(path: Path, fernet: Fernet) -> bytes:
    if path.is_symlink():
        raise RuntimeError("Refusing symlinked secret")
    if os.name != "nt" and path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise RuntimeError("Unsafe secret file permissions")
    return fernet.decrypt(path.read_bytes())


def worker_identity(fernet: Fernet):
    init_storage()
    if not IDENTITY_PATH.exists():
        key = Ed25519PrivateKey.generate()
        data = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")
        payload = {"worker_id": secrets.token_hex(16), "private_pem": data}
        write_encrypted(IDENTITY_PATH, json.dumps(payload).encode(), fernet)
    identity = json.loads(read_encrypted(IDENTITY_PATH, fernet).decode())
    private_key = serialization.load_pem_private_key(identity["private_pem"].encode(), password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise RuntimeError("Only Ed25519 worker keys are permitted")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{12,80}", identity["worker_id"]):
        raise RuntimeError("Invalid worker ID")
    return identity["worker_id"], private_key


def canonical(payload: dict) -> bytes:
    # Matches mobile-web/api/_lib/core.js canonical() (ASCII-escaped only when non-ASCII).
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def signed_post(path: str, payload: dict, worker_id: str, private_key: Ed25519PrivateKey) -> dict:
    if path not in ("/api/telegram-personal-sync", "/api/telegram-observation"):
        raise RuntimeError("Unsupported read-only endpoint")
    raw = canonical(payload)
    signature = base64.b64encode(private_key.sign(raw)).decode("ascii")
    headers = {"Content-Type": "application/json", "X-EQ-Signature": signature}
    req = urllib.request.Request(API_ORIGIN + path, data=raw, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status != 202:
                raise RuntimeError("Unexpected signed API response")
            return json.loads(response.read(100000).decode("utf-8"))
    except urllib.error.HTTPError as err:
        # Never log Telegram content, headers or authentication credentials.
        raise RuntimeError("Cloud observation rejected (HTTP " + str(err.code) + ")") from None


def telegram_client(api_id: int, api_hash: str, session: StringSession) -> TelegramClient:
    return TelegramClient(session, api_id, api_hash,
                          device_model="EdgeQuant private listener",
                          app_version="1.0",
                          auto_reconnect=True,
                          connection_retries=5)


async def login_private_host(api_id: int, api_hash: str, fernet: Fernet) -> None:
    """
    Initial consent is performed in a *private operator host terminal*, not Vercel.
    This CLI is unsuitable for customers to access directly or for publicly shared terminals.
    """
    if SESS_PATH.exists():
        raise RuntimeError("An encrypted session already exists; refuse to replace it")
    client = telegram_client(api_id, api_hash, StringSession())
    await client.connect()
    try:
        phone = getpass.getpass("Telegram phone (entered ONLY in private worker terminal): ").strip()
        if not phone or len(phone) > 32:
            raise RuntimeError("Invalid phone entry")
        await client.send_code_request(phone)
        code = getpass.getpass("Telegram login code (PRIVATE terminal, hidden): ").strip()
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            password = getpass.getpass("Telegram 2FA password (PRIVATE terminal, hidden): ")
            await client.sign_in(password=password)
            del password
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram did not authorize this private session")
        saved = client.session.save()
        if not saved or not isinstance(saved, str):
            raise RuntimeError("Telegram session could not be saved")
        write_encrypted(SESS_PATH, saved.encode("ascii"), fernet)
        print("Encrypted session created on isolated private worker. No phone code stored in cloud.")
    finally:
        await client.disconnect()


def dialog_from_entity(d) -> dict | None:
    entity = d.entity
    if not isinstance(entity, (Channel, Chat)):
        return None  # Never discover private one-to-one chats.
    cid = str(d.id)
    # Telethon Dialog.id uses 'marked' peer ids (-100 for channels; negative for basic groups).
    if not CHAT_RE.fullmatch(cid):
        return None
    is_channel = isinstance(entity, Channel)
    dtype = "supergroup" if is_channel and getattr(entity, "megagroup", False) else "channel" if is_channel else "group"
    label = re.sub(r"[\x00-\x1f\x7f<>]", "", str(getattr(d, "title", "") or "Unnamed chat")).strip()[:100]
    if not label:
        label = "Unnamed chat"
    return {"chat_id": cid, "dialog_type": dtype, "label": label}


async def sync_dialogs(client: TelegramClient, worker_id: str, private_key: Ed25519PrivateKey) -> set[str]:
    dialogs = []
    async for d in client.iter_dialogs():
        info = dialog_from_entity(d)
        if info:
            dialogs.append(info)
    # Even an empty list must produce signed heartbeat and update worker liveness.
    chunks = [dialogs[i:i + 100] for i in range(0, len(dialogs), 100)] or [[]]
    enabled: set[str] = set()
    for chunk in chunks:
        payload = {"dialogs": chunk, "event_id": secrets.token_hex(16),
                   "timestamp_ms": int(time.time() * 1000), "worker_id": worker_id}
        result = await asyncio.to_thread(
            signed_post, "/api/telegram-personal-sync", payload, worker_id, private_key
        )
        # Server returns ONLY user-approved, recently-discovered chat IDs.
        enabled.update(result.get("enabled_chat_ids", []))
    return enabled


async def monitor(api_id: int, api_hash: str, fernet: Fernet) -> None:
    if not SESS_PATH.exists():
        raise RuntimeError("No encrypted session. Run this script in 'login' mode privately first")
    worker_id, private_key = worker_identity(fernet)
    saved = read_encrypted(SESS_PATH, fernet).decode("ascii")
    client = telegram_client(api_id, api_hash, StringSession(saved))
    enabled_chats: set[str] = set()
    guard = asyncio.Semaphore(4)

    async def on_event(event, kind: str) -> None:
        chat_id = str(event.chat_id or "")
        if chat_id not in enabled_chats:
            return
        message = event.message
        text = str(message.raw_text or "")
        if not text or len(text) > 3000 or re.search(r"[\x00-\x08\x0b-\x1f\x7f]", text):
            return
        edit_ms = int(message.edit_date.timestamp() * 1000) if kind == "edit" and message.edit_date else (
            int(message.date.timestamp() * 1000) if kind == "edit" and message.date else 0
        )
        payload = {
            "chat_id": chat_id, "edit_date_ms": edit_ms, "event_id": secrets.token_hex(16),
            "kind": kind, "message_id": int(message.id),
            "reply_to_id": int(message.reply_to_msg_id or 0), "text": text,
            "timestamp_ms": int(time.time() * 1000), "worker_id": worker_id,
        }
        async with guard:
            try:
                await asyncio.to_thread(
                    signed_post, "/api/telegram-observation", payload, worker_id, private_key
                )
            except RuntimeError:
                # Fail closed; do not queue sensitive messages on disk.
                print("A read-only Telegram observation was not accepted.", file=sys.stderr)

    @client.on(events.NewMessage(incoming=True))
    async def new_message(event):
        await on_event(event, "new")

    @client.on(events.MessageEdited())
    async def edited_message(event):
        await on_event(event, "edit")

    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram session revoked or expired; re-authorize privately")
        while True:
            try:
                updated = await sync_dialogs(client, worker_id, private_key)
                enabled_chats.clear()
                enabled_chats.update(updated)
                print("Signed heartbeat accepted; enabled read-only sources:", len(enabled_chats))
            except Exception:
                enabled_chats.clear()
                print("Dialog heartbeat failed; all message uploading paused.", file=sys.stderr)
            await asyncio.sleep(SYNC_INTERVAL)
    finally:
        enabled_chats.clear()
        await client.disconnect()


async def run(mode: str) -> None:
    api_id, api_hash, fernet = env_settings()
    if mode == "identity":
        worker_id, private_key = worker_identity(fernet)
        pub = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        print("Worker ID (operator-only):", worker_id)
        print("Public key PEM (NOT a secret; operator must approve for the correct user):")
        print(pub)
    elif mode == "login":
        await login_private_host(api_id, api_hash, fernet)
    else:
        await monitor(api_id, api_hash, fernet)


def main():
    parser = argparse.ArgumentParser(description="EdgeQuant isolated personal Telegram read-only listener")
    parser.add_argument("mode", choices=["identity", "login", "listen"])
    args = parser.parse_args()
    try:
        asyncio.run(run(args.mode))
    except (RuntimeError, KeyboardInterrupt) as exc:
        print("Worker stopped:", str(exc) if isinstance(exc, RuntimeError) else "operator interrupt", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
