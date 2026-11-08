-- Windows managed worker pairing / token lifecycle. Agent tokens are stored as hashes only.
-- This migration is additive and preserves the phase-2 accounts and order rule prototype.
CREATE TABLE IF NOT EXISTS broker_pairing_requests (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  broker_account_id UUID NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
  token_hash CHAR(64) NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (broker_account_id)
);
CREATE INDEX IF NOT EXISTS ix_pairing_tenant ON broker_pairing_requests(tenant_id,expires_at);
CREATE TABLE IF NOT EXISTS broker_agents (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  broker_account_id UUID NOT NULL UNIQUE REFERENCES broker_accounts(id) ON DELETE CASCADE,
  worker_id VARCHAR(120) NOT NULL,
  token_hash CHAR(64) NOT NULL UNIQUE,
  observed_server VARCHAR(100) NOT NULL,
  observed_login VARCHAR(20) NOT NULL,
  terminal_connected BOOLEAN NOT NULL DEFAULT false,
  trade_allowed BOOLEAN NOT NULL DEFAULT false,
  last_seen_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_agents_tenant ON broker_agents(tenant_id,last_seen_at DESC);
