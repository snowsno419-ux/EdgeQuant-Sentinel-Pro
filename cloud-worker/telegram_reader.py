"""EdgeQuant read-only Telegram client. No MT5 trades, no signal publishing.

Requires explicit operator/user consent to monitor allowlisted Telegram groups.
Telethon login and its .session file remain on a secured Windows worker host.
Never run a shared Telegram account for multiple clients. Do not commit secrets.
"""
from __future__ import annotations
import asyncio, base64, json, os, re, secrets, time, urllib.request
from pathlib import Path
from urllib.parse import urlparse
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def safe_target(raw: str) -> bool:
    u=urlparse(raw)
    return ((u.scheme=='https') or (os.getenv('EDGEQUANT_ALLOW_LOCAL_DEV')=='1' and u.scheme=='http' and u.hostname in ('localhost','127.0.0.1'))) and u.path=='/api/telegram-observation' and not u.username and not u.password and not u.fragment


def packet(message, kind: str, worker_id: str) -> dict:
    if kind not in ('new','edit'): raise ValueError('Unsupported event kind')
    raw=(message.raw_text or '').strip()
    if not raw or len(raw)>3000 or re.search(r'[\x00-\x08\x0b-\x1f\x7f]',raw):raise ValueError('Invalid message')
    edit=int(message.edit_date.timestamp()*1000) if message.edit_date else 0
    return dict(worker_id=worker_id,chat_id=str(message.chat_id),message_id=int(message.id),reply_to_id=int(message.reply_to_msg_id or 0),text=raw,kind=kind,edit_date_ms=edit,event_id=secrets.token_urlsafe(18),timestamp_ms=int(time.time()*1000))


def push(url: str, p: dict, key):
    if not safe_target(url):raise ValueError('Use HTTPS EdgeQuant Telegram observation endpoint')
    raw=canonical(p);sig=base64.b64encode(key.sign(raw)).decode('ascii')
    req=urllib.request.Request(url,data=raw,headers={'Content-Type':'application/json','X-EQ-Signature':sig},method='POST')
    with urllib.request.urlopen(req,timeout=9) as response:return response.status


async def main():
    from telethon import TelegramClient, events
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    keys=['EQ_TELEGRAM_API_ID','EQ_TELEGRAM_API_HASH','EQ_TELEGRAM_SESSION_PATH','EQ_TELEGRAM_CHATS','EQ_TELEGRAM_WORKER_ID','EQ_CLOUD_TELEGRAM_ENDPOINT','EQ_WORKER_KEY_FILE']
    missing=[x for x in keys if not os.getenv(x)]
    if missing:raise RuntimeError('Missing locally configured env: '+', '.join(missing))
    chats={int(x.strip()) for x in os.getenv('EQ_TELEGRAM_CHATS','').split(',') if x.strip()}
    if not chats:raise RuntimeError('Telegram allowlist is empty')
    endpoint=os.environ['EQ_CLOUD_TELEGRAM_ENDPOINT']
    if not safe_target(endpoint):raise RuntimeError('Only HTTPS backend endpoint allowed')
    key=load_pem_private_key(Path(os.environ['EQ_WORKER_KEY_FILE']).read_bytes(),password=None)
    if not isinstance(key,Ed25519PrivateKey):raise RuntimeError('Expected Ed25519 private signing key')
    async with TelegramClient(os.environ['EQ_TELEGRAM_SESSION_PATH'],int(os.environ['EQ_TELEGRAM_API_ID']),os.environ['EQ_TELEGRAM_API_HASH']) as client:
        # User must complete an interactive Telegram OTP step locally on first use.
        await client.start()
        async def emit(event,kind):
            if int(event.chat_id) not in chats:return
            try:
                payload=packet(event.message,kind,os.environ['EQ_TELEGRAM_WORKER_ID'])
                await asyncio.to_thread(push,endpoint,payload,key)
            except Exception as e:
                print('Telegram read-only status error: '+type(e).__name__)
        @client.on(events.NewMessage(chats=list(chats)))
        async def new(e):await emit(e,'new')
        @client.on(events.MessageEdited(chats=list(chats)))
        async def edit(e):await emit(e,'edit')
        print('Telegram read-only listener started; no trade execution enabled')
        await client.run_until_disconnected()


if __name__=='__main__':asyncio.run(main())
