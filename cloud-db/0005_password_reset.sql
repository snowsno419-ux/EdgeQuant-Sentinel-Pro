-- EdgeQuant secure, single-use password recovery.
-- Add-only migration. Apply with the database owner after 0002_onboarding.sql.
CREATE TABLE IF NOT EXISTS password_reset_tokens (
  token_digest CHAR(64) PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_password_reset_expires ON password_reset_tokens(expires_at);
-- Preserve account role and TOTP; purge expired rows as part of the retention job.
