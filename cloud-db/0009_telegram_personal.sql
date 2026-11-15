-- EdgeQuant personal Telegram / MTProto read-only mode. No OTP/session storage in Vercel or Neon.
ALTER TABLE telegram_listener_requests
 ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'personal'
 CHECK (mode IN ('personal','bot'));
ALTER TABLE telegram_listener_requests
 ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS telegram_personal_dialogs (
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 chat_id TEXT NOT NULL CHECK (chat_id ~ '^(-100)?[0-9]{5,20}$'),
 label TEXT NOT NULL CHECK (length(label) BETWEEN 1 AND 100),
 dialog_type TEXT NOT NULL CHECK(dialog_type IN ('channel','group','supergroup')),
 enabled BOOLEAN NOT NULL DEFAULT FALSE,
 last_discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 PRIMARY KEY (user_id,chat_id)
);
CREATE INDEX IF NOT EXISTS idx_personal_dialogs_user ON telegram_personal_dialogs(user_id,enabled);
-- Sessions and login codes belong in an encrypted, isolated external listener, never these tables.
