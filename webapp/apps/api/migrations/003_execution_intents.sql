-- Phase 4 demo-only order ledger; isolate by tenant and broker account.
CREATE UNIQUE INDEX IF NOT EXISTS ux_broker_id_tenant ON broker_accounts(id,tenant_id);
ALTER TABLE broker_agents ADD COLUMN IF NOT EXISTS trade_mode VARCHAR(10) NOT NULL DEFAULT 'UNKNOWN'
 CHECK(trade_mode IN ('DEMO','REAL','CONTEST','UNKNOWN'));

CREATE TABLE IF NOT EXISTS order_intents (
 id UUID PRIMARY KEY,
 tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
 broker_account_id UUID NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
 source_mode VARCHAR(20) NOT NULL CHECK(source_mode IN ('TELEGRAM','DIRECT_MT5_COPY')),
 duplicate_digest CHAR(64) NOT NULL,
 source_identity VARCHAR(200) NOT NULL DEFAULT '',
 symbol VARCHAR(32) NOT NULL,
 side VARCHAR(10) NOT NULL CHECK(side IN ('BUY','SELL')),
 policy_version VARCHAR(60) NOT NULL,
 status VARCHAR(24) NOT NULL DEFAULT 'STAGED'
   CHECK(status IN ('STAGED','QUEUED','PARTIAL','COMPLETE','REJECTED','UNKNOWN_RECONCILE','CANCELLED')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(broker_account_id,duplicate_digest),
 UNIQUE(id,broker_account_id,tenant_id),
 FOREIGN KEY(broker_account_id,tenant_id) REFERENCES broker_accounts(id,tenant_id)
);
CREATE INDEX IF NOT EXISTS ix_order_intents_tenant_created ON order_intents(tenant_id,created_at DESC);

CREATE TABLE IF NOT EXISTS order_legs (
 id UUID PRIMARY KEY,
 tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
 broker_account_id UUID NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
 intent_id UUID NOT NULL,
 layer SMALLINT NOT NULL CHECK(layer BETWEEN 1 AND 2),
 request_payload JSONB NOT NULL,
 status VARCHAR(24) NOT NULL DEFAULT 'QUEUED'
   CHECK(status IN ('STAGED','QUEUED','LEASED','BROKER_ACCEPTED','BROKER_REJECTED','LOCAL_REJECTED','UNKNOWN_RECONCILE','CANCELLED')),
 lease_token_hash CHAR(64),
 lease_expires_at TIMESTAMPTZ,
 claimed_by_agent UUID REFERENCES broker_agents(id) ON DELETE SET NULL,
 attempts INT NOT NULL DEFAULT 0 CHECK(attempts >= 0 AND attempts <= 1),
 broker_ticket BIGINT,
 broker_retcode INT,
 broker_message VARCHAR(320),
 completed_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 FOREIGN KEY(intent_id,broker_account_id,tenant_id) REFERENCES order_intents(id,broker_account_id,tenant_id) ON DELETE CASCADE,
 UNIQUE(intent_id,layer)
);
CREATE INDEX IF NOT EXISTS ix_order_legs_dispatch ON order_legs(broker_account_id,status,created_at) WHERE status='QUEUED';
CREATE INDEX IF NOT EXISTS ix_order_legs_lease ON order_legs(status,lease_expires_at) WHERE status='LEASED';
CREATE INDEX IF NOT EXISTS ix_order_legs_tenant ON order_legs(tenant_id,created_at DESC);

CREATE TABLE IF NOT EXISTS execution_events (
 id UUID PRIMARY KEY,
 tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
 broker_account_id UUID NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
 intent_id UUID NOT NULL REFERENCES order_intents(id) ON DELETE CASCADE,
 leg_id UUID REFERENCES order_legs(id) ON DELETE CASCADE,
 event_type VARCHAR(36) NOT NULL,
 event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
 FOREIGN KEY(broker_account_id,tenant_id) REFERENCES broker_accounts(id,tenant_id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_execution_events_intent ON execution_events(intent_id,created_at);
