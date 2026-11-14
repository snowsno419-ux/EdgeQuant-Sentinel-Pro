-- EdgeQuant Cloud Phase 4.0 READ-ONLY integration schema.
-- Apply only in a private, managed PostgreSQL database. Never publish passwords or keys.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS users (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN('receiver','provider')),
 email_verified BOOLEAN NOT NULL DEFAULT FALSE,
 totp_secret TEXT, locked_until TIMESTAMPTZ, failed_logins INT NOT NULL DEFAULT 0, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
 token_digest CHAR(64) PRIMARY KEY,user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS broker_accounts (
 id TEXT PRIMARY KEY CHECK(length(id) BETWEEN 12 AND 80),user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 label TEXT NOT NULL,broker TEXT NOT NULL,server TEXT NOT NULL,login_hint TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),UNIQUE(user_id,server,login_hint)
);
CREATE TABLE IF NOT EXISTS worker_keys (
 id TEXT PRIMARY KEY CHECK(length(id) BETWEEN 12 AND 80),broker_id TEXT NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
 public_key_pem TEXT NOT NULL,revoked_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS worker_event_ids (
 worker_id TEXT NOT NULL REFERENCES worker_keys(id) ON DELETE CASCADE,event_id TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),PRIMARY KEY(worker_id,event_id)
);
CREATE TABLE IF NOT EXISTS broker_snapshots (
 broker_id TEXT PRIMARY KEY REFERENCES broker_accounts(id) ON DELETE CASCADE,
 observed_at BIGINT NOT NULL,balance NUMERIC(16,2) NOT NULL,equity NUMERIC(16,2) NOT NULL,
 floating NUMERIC(16,2) NOT NULL,open_positions INT NOT NULL,pending_orders INT NOT NULL,
 terminal_connected BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON broker_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_worker_events_created ON worker_event_ids(created_at);
-- Automated retention job must purge old worker_event_ids and expired sessions.
-- DB role used by Vercel must NOT own the database or have schema-admin privileges.
