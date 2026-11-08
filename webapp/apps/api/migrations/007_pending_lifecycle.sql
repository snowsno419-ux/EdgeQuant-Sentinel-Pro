-- Phase 7A: DEMO pending MODIFY/CANCEL requires original OPEN provenance.
-- One-time lease/status columns were created in 006; this migration does not send trades.
ALTER TABLE copy_ticket_mappings
 ADD COLUMN IF NOT EXISTS original_open_delivery_id UUID REFERENCES copy_delivery_intents(id),
 ADD COLUMN IF NOT EXISTS mapped_order_type VARCHAR(12),
 ADD COLUMN IF NOT EXISTS filled_position_ticket VARCHAR(19),
 ADD COLUMN IF NOT EXISTS reconciled_at TIMESTAMPTZ;
ALTER TABLE copy_ticket_mappings DROP CONSTRAINT IF EXISTS copy_ticket_mappings_state_check;
ALTER TABLE copy_ticket_mappings ADD CONSTRAINT copy_ticket_mappings_state_check
 CHECK(state IN ('ACTIVE','FILLED_HOLD','CLOSED','CANCELLED','NEEDS_RECONCILE'));
CREATE INDEX IF NOT EXISTS ix_copy_followup_claim
 ON copy_delivery_intents(receiver_broker_account_id,status,recorded_at)
 WHERE action IN ('MODIFY','CANCEL') AND status IN ('STAGED','WAITING_TICKET_MAPPING','LEASED');
-- Legacy rows without original OPEN provenance cannot be auto-modified or canceled.
