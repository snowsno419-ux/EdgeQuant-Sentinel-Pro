-- Safe self-service pairing for a separate Windows read-only MetaTrader 5 DEMO worker.
-- Passwords and MT5 terminal files NEVER enter EdgeQuant web or database.
CREATE TABLE IF NOT EXISTS mt5_worker_pairings (
 broker_id TEXT PRIMARY KEY REFERENCES broker_accounts(id) ON DELETE CASCADE,
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 token_digest CHAR(64) NOT NULL UNIQUE,
 expires_at TIMESTAMPTZ NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('PENDING','CLAIMED','APPROVED')) DEFAULT 'PENDING',
 claimed_worker_id TEXT,
 claimed_public_key_pem TEXT,
 claimed_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS mt5_worker_pairings_exp ON mt5_worker_pairings(expires_at);
-- Revoke worker_keys separately when decommissioning a terminal.
