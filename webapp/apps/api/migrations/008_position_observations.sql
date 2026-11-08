-- Phase 7B1 read-only receiver pending -> position correlation.
-- This does NOT enable any market, modify, partial-close or close actions.
ALTER TABLE copy_ticket_mappings
  ADD COLUMN IF NOT EXISTS filled_position_identifier VARCHAR(19),
  ADD COLUMN IF NOT EXISTS position_observed_volume NUMERIC(22,8),
  ADD COLUMN IF NOT EXISTS position_last_observed_at TIMESTAMPTZ;
ALTER TABLE copy_ticket_mappings ADD CONSTRAINT position_identifier_positive
 CHECK(filled_position_identifier IS NULL OR filled_position_identifier ~ '^[1-9][0-9]{0,18}$');
CREATE UNIQUE INDEX IF NOT EXISTS ux_copy_mapping_tenant_broker
 ON copy_ticket_mappings(id,receiver_tenant_id,receiver_broker_account_id);
CREATE TABLE IF NOT EXISTS copy_position_observations (
 id UUID PRIMARY KEY,
 mapping_id UUID NOT NULL REFERENCES copy_ticket_mappings(id) ON DELETE CASCADE,
 receiver_tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
 receiver_broker_account_id UUID NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
 broker_order_ticket VARCHAR(19) NOT NULL,
 FOREIGN KEY(mapping_id,receiver_tenant_id,receiver_broker_account_id)
   REFERENCES copy_ticket_mappings(id,receiver_tenant_id,receiver_broker_account_id) ON DELETE CASCADE,
 status VARCHAR(28) NOT NULL CHECK(status IN ('STILL_PENDING','FILLED_POSITION_OBSERVED','UNKNOWN_RECONCILE')),
 position_identifier VARCHAR(19),
 position_ticket VARCHAR(19),
 observed_volume NUMERIC(22,8),
 note VARCHAR(180) NOT NULL,
 observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CHECK ((status='FILLED_POSITION_OBSERVED' AND position_identifier IS NOT NULL
         AND position_ticket IS NOT NULL AND observed_volume>0) OR
        (status<>'FILLED_POSITION_OBSERVED' AND position_identifier IS NULL
         AND position_ticket IS NULL AND observed_volume IS NULL))
);
CREATE INDEX IF NOT EXISTS ix_pos_observations_mapping_time
 ON copy_position_observations(mapping_id,observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_pos_observations_tenant_time
 ON copy_position_observations(receiver_tenant_id,observed_at DESC);
