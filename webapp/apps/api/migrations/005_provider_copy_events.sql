-- Phase 5. Provider -> receiver copy INTENT STAGING ONLY. NEVER executes a trade.
-- Every cross-tenant relationship is deliberate, consented, and constrained by composite FKs.
CREATE TABLE IF NOT EXISTS provider_copy_services (
  id UUID PRIMARY KEY,
  provider_tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  provider_broker_account_id UUID NOT NULL,
  name VARCHAR(80) NOT NULL,
  status VARCHAR(12) NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('DRAFT','ACTIVE','PAUSED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(provider_broker_account_id,provider_tenant_id) REFERENCES broker_accounts(id,tenant_id),
  UNIQUE(id,provider_tenant_id),
  UNIQUE(id,provider_broker_account_id,provider_tenant_id)
);
CREATE INDEX IF NOT EXISTS ix_copy_services_provider ON provider_copy_services(provider_tenant_id,status);

CREATE TABLE IF NOT EXISTS copy_subscriptions (
  id UUID PRIMARY KEY,
  provider_service_id UUID NOT NULL,
  provider_tenant_id UUID NOT NULL,
  receiver_tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  receiver_broker_account_id UUID NOT NULL,
  status VARCHAR(12) NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','PAUSED','CANCELLED')),
  lot_mode VARCHAR(12) NOT NULL CHECK(lot_mode IN ('SAME','FIXED','MULTIPLIER')),
  lot_value NUMERIC(22,8),
  max_lot NUMERIC(22,8) NOT NULL CHECK(max_lot>0),
  consented_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK(receiver_tenant_id<>provider_tenant_id),
  CHECK((lot_mode='SAME' AND lot_value IS NULL) OR (lot_mode IN ('FIXED','MULTIPLIER') AND lot_value>0)),
  FOREIGN KEY(provider_service_id,provider_tenant_id) REFERENCES provider_copy_services(id,provider_tenant_id) ON DELETE RESTRICT,
  FOREIGN KEY(receiver_broker_account_id,receiver_tenant_id) REFERENCES broker_accounts(id,tenant_id) ON DELETE RESTRICT,
  UNIQUE(provider_service_id,receiver_broker_account_id),
  UNIQUE(id,receiver_tenant_id,receiver_broker_account_id),
  UNIQUE(id,provider_service_id,receiver_tenant_id,receiver_broker_account_id)
);
CREATE INDEX IF NOT EXISTS ix_copy_subscriptions_receiver ON copy_subscriptions(receiver_tenant_id,status);
CREATE INDEX IF NOT EXISTS ix_copy_subscriptions_service ON copy_subscriptions(provider_service_id,status);

CREATE TABLE IF NOT EXISTS copy_provider_events (
  id UUID PRIMARY KEY,
  provider_service_id UUID NOT NULL,
  provider_tenant_id UUID NOT NULL,
  provider_broker_account_id UUID NOT NULL,
  provider_event_id VARCHAR(128) NOT NULL,
  provider_order_id VARCHAR(19) NOT NULL,
  revision INTEGER NOT NULL CHECK(revision>0),
  event_type VARCHAR(16) NOT NULL CHECK(event_type IN ('OPEN','MODIFY','PARTIAL_CLOSE','CLOSE','CANCEL')),
  fingerprint CHAR(64) NOT NULL,
  event_payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(provider_service_id,provider_broker_account_id,provider_tenant_id)
    REFERENCES provider_copy_services(id,provider_broker_account_id,provider_tenant_id),
  UNIQUE(provider_service_id,provider_event_id),
  UNIQUE(provider_service_id,provider_order_id,revision),
  UNIQUE(id,provider_service_id)
);
CREATE INDEX IF NOT EXISTS ix_copy_events_order ON copy_provider_events(provider_service_id,provider_order_id,revision DESC);

CREATE TABLE IF NOT EXISTS copy_ticket_mappings (
  id UUID PRIMARY KEY,
  provider_service_id UUID NOT NULL REFERENCES provider_copy_services(id) ON DELETE RESTRICT,
  provider_order_id VARCHAR(19) NOT NULL,
  subscription_id UUID NOT NULL,
  receiver_tenant_id UUID NOT NULL,
  receiver_broker_account_id UUID NOT NULL,
  receiver_ticket VARCHAR(19) NOT NULL CHECK(receiver_ticket ~ '^[1-9][0-9]{0,18}$'),
  state VARCHAR(12) NOT NULL DEFAULT 'ACTIVE' CHECK(state IN ('ACTIVE','CLOSED','CANCELLED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(subscription_id,provider_service_id,receiver_tenant_id,receiver_broker_account_id)
    REFERENCES copy_subscriptions(id,provider_service_id,receiver_tenant_id,receiver_broker_account_id),
  UNIQUE(provider_service_id,provider_order_id,subscription_id),
  UNIQUE(receiver_broker_account_id,receiver_ticket)
);

CREATE TABLE IF NOT EXISTS copy_delivery_intents (
  id UUID PRIMARY KEY,
  provider_event_id UUID NOT NULL,
  provider_service_id UUID NOT NULL,
  subscription_id UUID NOT NULL,
  receiver_tenant_id UUID NOT NULL,
  receiver_broker_account_id UUID NOT NULL,
  action VARCHAR(16) NOT NULL CHECK(action IN ('OPEN','MODIFY','PARTIAL_CLOSE','CLOSE','CANCEL')),
  status VARCHAR(32) NOT NULL CHECK(status IN ('STAGED','WAITING_TICKET_MAPPING','BLOCKED_RISK','CANCELLED')),
  request_payload JSONB NOT NULL,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(provider_event_id,provider_service_id)
    REFERENCES copy_provider_events(id,provider_service_id) ON DELETE RESTRICT,
  FOREIGN KEY(subscription_id,provider_service_id,receiver_tenant_id,receiver_broker_account_id)
    REFERENCES copy_subscriptions(id,provider_service_id,receiver_tenant_id,receiver_broker_account_id),
  UNIQUE(provider_event_id,subscription_id)
);
CREATE INDEX IF NOT EXISTS ix_copy_delivery_receiver ON copy_delivery_intents(receiver_tenant_id,recorded_at DESC);
-- No trigger/job can dispatch COPY intents in this milestone.
