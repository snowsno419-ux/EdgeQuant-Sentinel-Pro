-- EdgeQuant Cloud: allow account owners to request managed Telegram listener provisioning.
-- No phone numbers, OTPs, session tokens or Telegram authorization secrets are stored here.
-- Operator must approve and provision listener separately; LIVE trading remains disabled.
CREATE TABLE IF NOT EXISTS telegram_listener_requests (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
 state TEXT NOT NULL DEFAULT 'PENDING'
   CHECK(state IN ('PENDING','APPROVED','PROVISIONING','CONNECTED','FAILED','CANCELLED')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_telegram_listener_requests_created ON telegram_listener_requests(created_at);
