# EdgeQuant Cloud — Windows DEMO workers / Telegram read-only listener

This folder is a **development adapter** for secured, isolated Windows cloud worker hosts (not a 24/7 hosted service). Existing EdgeQuant Neon Dark PC trading code is deliberately untouched.

## DEMO MT5 read-only worker

Requires a managed Windows 10/11 x64 worker (not a phone), an installed and manually logged-in DEMO MT5 terminal, Python, and `MetaTrader5` plus `cryptography`. The program calls `mt5.initialize`, `account_info`, `terminal_info`, `positions_total`, and `orders_total`. It never calls `mt5.login`, `order_send`, or trade-close APIs. It refuses non-DEMO accounts and broker login/server mismatch.

- User signs up and verifies email + 2FA; adds broker metadata in web UI. Worker request is stored as **PENDING**, not automatically executed.
- Operator separately approves/provisions a worker host and creates an Ed25519 private key using `generate_signing_key.py --private-path PATH --public-path PATH`. **Private key remains on that host.** Windows admin should restrict file with NTFS ACLs (`icacls`) because `chmod` alone does not establish Windows file ACL isolation.
- Operator (not browser) inserts `worker_keys(id,broker_id,public_key_pem)` into private Postgres after verifying the requested broker, and configures each environment variable in `read_only_mt5.py`. Worker IDs and broker IDs are UUIDs / URL-safe identifiers, *not* passwords.
- Worker sends HTTPS signed snapshots to `/api/worker-observation`. UI renders metrics only when the signature validates, broker account identity matches, and timestamp is fresh.
- Dedicated Windows worker sessions and MT5 terminal directories are required per client or isolated account; do not run unrelated client accounts in one shared MT5 session.

## Telegram read-only signal inbox

- Each client's Telegram account requires **explicit authorization**, with Telethon session file stored on its assigned, secured worker host, never in Vercel or Git.
- Only allowlisted Telegram chat IDs are read. Account owner registers source metadata in UI; an operator independently marks source enabled and configures a `telegram_listener_keys` PUBLIC key after consent.
- `telegram_reader.py` forwards new messages and edits with original `chat_id`, `message_id`, and `reply_to_id` through signed HTTPS payloads. Local Telegram phone OTP/2FA is entered directly into the worker's authenticated console; never into a public dashboard.
- API keeps messages private per user. **No signal parser or trade execution has been connected to the inbox.** Cancel/Close replies are stored but do not trigger broker operations yet.

## Required testing before any automation

Real DEMO Windows terminal and broker validation; MT5 bridge restart/reconnect; Telegram event correlation and edits; replay/reordering; broker-specific pip/digits/volume and exact entries; exactly two layers or selected layer count; idempotency across MT5 accounts; cancellation and close by original Telegram message; first-touch market fallback; SL/TP modification; Auto BE OFF; daily risk limits; operator audit and emergency kill switch; recovery after VM failure; 100-client isolated load test.

Neither GitHub nor Vercel itself runs a Windows MetaTrader terminal continuously. Paid Windows worker infrastructure must be selected and approved separately before PC-free end-to-end trading is possible.
