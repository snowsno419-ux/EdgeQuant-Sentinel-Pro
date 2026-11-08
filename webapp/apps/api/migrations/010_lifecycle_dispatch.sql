-- Phase 7B2B: separate DEMO lifecycle opt-ins were added as DEFAULT FALSE in migration 009.
-- Reuse Phase-6 single-use lease / status fields; NO DB trigger sends orders.
-- API blocks production dispatch unconditionally, and Windows worker verifies DEMO/hedging.
CREATE INDEX IF NOT EXISTS ix_copy_market_open_claim
 ON copy_delivery_intents(receiver_broker_account_id,status,recorded_at)
 WHERE action='OPEN' AND status IN ('STAGED','LEASED');
CREATE INDEX IF NOT EXISTS ix_copy_position_claim
 ON copy_delivery_intents(receiver_broker_account_id,status,recorded_at)
 WHERE action IN ('MODIFY','PARTIAL_CLOSE','CLOSE') AND status IN ('STAGED','WAITING_TICKET_MAPPING','LEASED');
CREATE INDEX IF NOT EXISTS ix_receiver_position_mapping_provenance
 ON copy_ticket_mappings(receiver_broker_account_id,filled_position_identifier)
 WHERE filled_position_identifier IS NOT NULL;
