-- Phase 8A/8B additive broker telemetry schema (NOT applied to PostgreSQL).
-- Only future authenticated, tenant/account-bound worker ingestion may populate this.
CREATE UNIQUE INDEX IF NOT EXISTS ux_broker_accounts_tenant_id ON broker_accounts(id,tenant_id);
CREATE TABLE IF NOT EXISTS broker_analytics_snapshots (
 id UUID PRIMARY KEY,
 tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
 broker_account_id UUID NOT NULL,
 broker_agent_id UUID NOT NULL REFERENCES broker_agents(id) ON DELETE RESTRICT,
 source VARCHAR(16) NOT NULL DEFAULT 'MT5_WORKER' CHECK(source='MT5_WORKER'),
 observed_at TIMESTAMPTZ NOT NULL,
 received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 account_currency VARCHAR(8) NOT NULL,
 balance NUMERIC(22,6) NOT NULL,
 equity NUMERIC(22,6) NOT NULL,
 margin NUMERIC(22,6) NOT NULL CHECK(margin >= 0),
 free_margin NUMERIC(22,6) NOT NULL,
 realized_today NUMERIC(22,6) NOT NULL,
 floating_pnl NUMERIC(22,6) NOT NULL,
 open_positions INTEGER NOT NULL CHECK(open_positions >= 0),
 pending_orders INTEGER NOT NULL CHECK(pending_orders >= 0),
 quotes JSONB NOT NULL DEFAULT '[]'::jsonb CHECK(jsonb_typeof(quotes)='array'),
 FOREIGN KEY(broker_account_id,tenant_id) REFERENCES broker_accounts(id,tenant_id) ON DELETE CASCADE,
 UNIQUE(broker_account_id,observed_at)
);
CREATE INDEX IF NOT EXISTS ix_broker_analytics_latest ON broker_analytics_snapshots(tenant_id,broker_account_id,observed_at DESC);
-- A stored snapshot can become stale or disconnected. Never label it LIVE without a
-- current broker worker heartbeat and a quote timestamp freshness check.
