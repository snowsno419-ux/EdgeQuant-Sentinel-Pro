-- Phase 6: receiver-consented Direct MT5 pending OPEN demo leases only.
ALTER TABLE copy_subscriptions
  ADD COLUMN IF NOT EXISTS demo_pending_copy_enabled BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE copy_delivery_intents DROP CONSTRAINT IF EXISTS copy_delivery_intents_status_check;
ALTER TABLE copy_delivery_intents ADD CONSTRAINT copy_delivery_intents_status_check
  CHECK(status IN ('STAGED','WAITING_TICKET_MAPPING','BLOCKED_RISK','CANCELLED',
    'LEASED','BROKER_ACCEPTED','BROKER_REJECTED','LOCAL_REJECTED','UNKNOWN_RECONCILE'));
ALTER TABLE copy_delivery_intents
  ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts BETWEEN 0 AND 1),
  ADD COLUMN IF NOT EXISTS lease_token_hash CHAR(64),
  ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS claimed_by_agent UUID REFERENCES broker_agents(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS broker_ticket VARCHAR(19),
  ADD COLUMN IF NOT EXISTS broker_retcode INTEGER,
  ADD COLUMN IF NOT EXISTS broker_message VARCHAR(320),
  ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_copy_demo_dispatch
  ON copy_delivery_intents(receiver_broker_account_id,status,recorded_at)
  WHERE action='OPEN' AND status IN ('STAGED','LEASED');
-- No trigger auto-sends copy orders.
