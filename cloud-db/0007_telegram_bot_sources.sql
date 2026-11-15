-- EdgeQuant opt-in Telegram BOT mode: authenticated webhook, verified channel ownership, read-only messages.
-- Bot-based source access is narrower than Telegram account/MTProto login: bot must be added to chat.
ALTER TABLE telegram_sources ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;
ALTER TABLE telegram_sources ADD COLUMN IF NOT EXISTS last_observed_at TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS telegram_source_claims (
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 chat_id TEXT NOT NULL,
 code_digest CHAR(64) NOT NULL,
 expires_at TIMESTAMPTZ NOT NULL,
 PRIMARY KEY(user_id,chat_id),
 FOREIGN KEY(user_id,chat_id) REFERENCES telegram_sources(user_id,chat_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS telegram_source_claims_exp ON telegram_source_claims(expires_at);
CREATE TABLE IF NOT EXISTS telegram_bot_updates (
 update_id BIGINT PRIMARY KEY,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS telegram_bot_updates_created ON telegram_bot_updates(created_at);
-- Retain update ids for at least 7 days; no phone codes, bot token or account passwords stored.
