-- Telegram LIMIT -> STOP fallback audit (demo only).
-- Original order request remains immutable; record the actual broker request type and result.
ALTER TABLE order_legs ADD COLUMN IF NOT EXISTS submitted_order_type VARCHAR(12)
 CHECK (submitted_order_type IN ('BUY_LIMIT','SELL_LIMIT','BUY_STOP','SELL_STOP'));
ALTER TABLE order_legs ADD COLUMN IF NOT EXISTS fallback_attempted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE order_legs ADD COLUMN IF NOT EXISTS limit_rejection_retcode INTEGER;
CREATE INDEX IF NOT EXISTS ix_order_legs_fallback ON order_legs(broker_account_id,created_at DESC)
 WHERE fallback_attempted = true;
