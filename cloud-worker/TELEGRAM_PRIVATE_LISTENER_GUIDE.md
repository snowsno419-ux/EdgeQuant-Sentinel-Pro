# Private Telegram MTProto Listener — Secure Operator Setup

This source is a **staged, read-only host worker** for EdgeQuant Sentinel Pro. The request shown as **PROVISIONING REQUEST PENDING** is correctly stored, but **no server is currently running this worker**.

## Where it runs

- **NOT on Vercel and NOT on the customer's phone.** Telethon must run persistently on an isolated always-on Python cloud host; one encrypted Telegram session is isolated per consenting customer.
- No paid VPS, Railway or Windows machine is activated by adding this file to GitHub.
- This first version uses **private-host terminal login for the account owner/developer only**, not customer self-service OTP. Do not ask customers to give an operator their Telegram login codes or 2FA passwords.
- Browser login with phone OTP/2FA needs a separate authenticated, encrypted, time-limited remote challenge relay and explicit consent; **not implemented**.

## Implementation

File: `cloud-worker/telegram_personal_worker.py`; Python 3.11+. In the isolated Linux host's private shell:

```bash
python -m pip install telethon cryptography
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Store the **result privately in your secret manager**, NOT in source code, screenshots, chat, shell history or GitHub. Configure these host-only environment variables:

| Variable | Meaning |
|---|---|
| `EQ_TG_API_ID` | App API ID from your Telegram developer registration |
| `EQ_TG_API_HASH` | App API Hash from your Telegram developer registration |
| `EQ_TG_ENCRYPTION_KEY` | Fernet key held by worker secret manager |
| `EQ_PRIVATE_DATA_DIR` | Private, per-user storage directory (0700 mode) |

Get Telegram developer credentials at `https://my.telegram.org`. Never place the API hash, Telegram session, phone code, 2FA password, or Fernet key in Vercel's public browser JS, Neon database, GitHub files, support chats or client screenshots.

### Operator-host test (only with your own Telegram account)

Run `python cloud-worker/telegram_personal_worker.py identity` on the private host. It generates an **encrypted local Ed25519 key** and prints its **public key only**. The operator must verify the pending client's own request and approve that specific public key for that user's `telegram_listener_keys` row and update their `telegram_listener_requests` state to `APPROVED` using private administrative access.

Run `python cloud-worker/telegram_personal_worker.py login`. The **owner** types phone, code and optional Telegram 2FA into the **private host terminal**. This is not yet a flow suitable for paying mobile-only clients. The encrypted Telegram authorization session is written locally with strict permissions, never uploaded to Neon.

Run `python cloud-worker/telegram_personal_worker.py listen`. Signed heartbeat `POST /api/telegram-personal-sync` populates channel/group discovery, and returns only that account's **approved ON** chat IDs. The listener forwards read-only new/edited text only from that approved selection to `POST /api/telegram-observation`. The server separately validates account ID, signed worker identity, 10-minute heartbeat freshness, user-selected chat and event replay.

The user then sees **WORKER ONLINE** (after an accepted signed heartbeat), a list of their groups/channels, and can turn individual channels ON/OFF. The worker refreshes selection every 120 seconds. **Turning a channel OFF blocks database storage immediately, but the host may continue sending unwanted requests for at most 120 seconds until refresh**; tune this before real client deployment.

To revoke, use the in-app **DISCONNECT & REVOKE**, then on the private worker run `python cloud-worker/telegram_personal_worker.py logout` and destroy the worker's per-user secret material and ephemeral storage (follow the hosting provider's secure-data-retention policy). Changing user consent in the app alone does not erase encrypted copies on remote infrastructure.

## Before opening for 100 mobile-only clients

1. Build authenticated mobile-phone login/OTP/2FA relay **directly to the isolated private worker**, with temporary encrypted challenges, protected websocket or equivalent and strict rate limits; never send OTPs to Vercel/Neon or a support chat.
2. Build customer-approved public-key pairing/provisioning; don't manually enroll worker keys for a public customer base.
3. Use per-user isolation, session encryption, robust host monitoring, process restarts, quotas, GDPR/data retention review and remote revocation.
4. Verify with a consenting developer-owned Telegram account before exposing the workflow. Do not claim the screenshot's Pending status is connected until a signed heartbeat is observed.
5. Telegram read-only mode must stay OFF for order execution. MT5 accounts still need separate Windows terminal hosts; Vercel cannot run MT5.

Sources: [Telethon session docs](https://docs.telethon.dev/en/stable/concepts/sessions.html), [Telegram API registration](https://core.telegram.org/api/obtaining_api_id).
