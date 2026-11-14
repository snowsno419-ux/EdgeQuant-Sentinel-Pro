-- EdgeQuant Cloud Phase 6: per-user Telegram read-only signed ingress (NO trading).
CREATE TABLE IF NOT EXISTS telegram_sources (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 chat_id TEXT NOT NULL,label TEXT NOT NULL,kind TEXT NOT NULL CHECK(kind IN('LIMIT','MARKET')),
 enabled BOOLEAN NOT NULL DEFAULT FALSE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(user_id,chat_id)
);
CREATE TABLE IF NOT EXISTS telegram_listener_keys (
 id TEXT PRIMARY KEY CHECK(length(id) BETWEEN 12 AND 80),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 public_key_pem TEXT NOT NULL,revoked_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS telegram_event_ids (
 worker_id TEXT NOT NULL REFERENCES telegram_listener_keys(id) ON DELETE CASCADE,
 event_id TEXT NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),PRIMARY KEY(worker_id,event_id)
);
CREATE TABLE IF NOT EXISTS telegram_inbox (
 id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 chat_id TEXT NOT NULL,message_id BIGINT NOT NULL,reply_to_id BIGINT NOT NULL DEFAULT 0,
 edit_date_ms BIGINT NOT NULL DEFAULT 0,kind TEXT NOT NULL CHECK(kind IN('new','edit')),
 body TEXT NOT NULL CHECK(length(body)<=3000),observed_at_ms BIGINT NOT NULL,
 UNIQUE(user_id,chat_id,message_id,edit_date_ms)
);
CREATE INDEX IF NOT EXISTS idx_telegram_inbox_user ON telegram_inbox(user_id,id DESC);
CREATE INDEX IF NOT EXISTS idx_telegram_event_created ON telegram_event_ids(created_at);
-- Listener keys must be provisioned by the operator after verifying user consent.
-- Never store Telegram login codes, passwords or Telethon session bytes in this database.
