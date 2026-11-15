# EdgeQuant Sentinel Pro — Personal Telegram Account Connection (Primary)

**Mode selection:** Personal Telegram (MTProto) is primary for Receiver and Provider users. Telegram Bot mode is optional.

## User experience

1. Sign in to EdgeQuant Cloud using verified email, password and app 2FA.
2. Dashboard → **Personal Telegram → SET UP TELEGRAM**.
3. Press **REQUEST PERSONAL TELEGRAM CONNECTION**. This saves a private request without a Telegram phone number, OTP, password or session.
4. Once an independently hosted, encrypted per-user MTProto listener has been provisioned and the owner has securely authorized it, the listener's signed heartbeat lists joined public/private channels and groups belonging to that Telegram account.
5. The user selects or turns OFF each permitted source independently. Only enabled sources can send signed, read-only message updates to their own inbox.
6. **DISCONNECT & REVOKE** disables all personal sources and revokes worker keys in the cloud database. The host operator must also terminate the Telegram session on the worker and delete the encrypted local credentials.

## Current implementation

- Database: `cloud-db/0009_telegram_personal.sql`, with separate `telegram_personal_dialogs` and selected flags. **No Telegram credentials, 2FA codes or StringSessions are stored in Neon.**
- Signed worker API: POST `/api/telegram-personal-sync`, Ed25519 signature via `x-eq-signature`. Worker public keys must be provisioned per account after verification; the API rejects unapproved or revoked workers.
- Authenticated owner API: GET/POST `/api/telegram-personal-dialogs`; POST `/api/telegram-personal-disconnect`; GET/POST `/api/telegram-listener-requests`.
- Signed messages: existing POST `/api/telegram-observation`, now restricted to the matching owner's selected, fresh dialog and verified personal listener key.
- Replay guard: unique worker event IDs. Signed heartbeat freshness: 10 minutes. Expired/offline listeners cannot enable new dialogs or submit messages.
- Live trading stays OFF; Telegram messages are saved only as read-only observations.
- Personal source list is never fabricated from browser drafts or Telegram Bot channel claims.

## Not implemented / operator prerequisites

**Personal phone-code/2FA self-service login is NOT available yet.** It requires a real, persistent and hardened cloud listener host, secure per-user encrypted Telegram sessions, explicit user consent, abuse limits, Telegram API credentials, secure login challenge transport, a way to revoke remote auth, and an end-to-end verified test. Vercel serverless pages alone cannot hold a long-lived MTProto client.

The operator must register a Telegram developer application through https://my.telegram.org → API development tools and use its application `api_id`/`api_hash` privately on the listener host. Do not paste these credentials into a GitHub repo, ChatGPT chat, browser localStorage or email. A Telegram session string acts as an account authorization token and should never be printed, copied or shared.

Telegram's API terms and anti-abuse limits apply: https://core.telegram.org/api/obtaining_api_id. Official authorization flow: https://core.telegram.org/api/auth.

## Architecture for mobile-only clients (~100 accounts)

One user → one authorized account scope and isolated encrypted Telegram session (in a separately hosted worker). The worker performs Telegram login, dialog discovery and event listening with user consent. All requests to the cloud API are signed with that user-worker's Ed25519 key, and never carry account phone number, OTP, 2FA password or session data. Worker provisioning and hosting remain staged (no paid service activated).

MT5 requires its own independent Windows terminal/worker for each isolated client/broker. No live trades are placed while this cloud integration is incomplete.

## Current migration

Apply `0009_telegram_personal.sql` additively after prior cloud database migrations. Do not enable Telegram phone/OTP input forms until a properly deployed, encrypted private worker can receive and process those challenges without storing OTPs in logs, caches or the shared database.
