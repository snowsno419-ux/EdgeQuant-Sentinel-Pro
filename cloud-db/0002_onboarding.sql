-- EdgeQuant Cloud Phase 6: verified email onboarding + rate limiting + TOTP enrollment.
-- Run after 0001_readonly_schema.sql with owner role via Neon/Vercel dashboard SQL editor.
-- Do not put the DATABASE_URL in Git or chat.
ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_pending TEXT;
CREATE TABLE IF NOT EXISTS verification_tokens (
  token_digest CHAR(64) PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS enrollment_sessions (
  token_digest CHAR(64) PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_throttle (
  bucket CHAR(64) PRIMARY KEY,
  hits INTEGER NOT NULL DEFAULT 1,
  window_start TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_verification_exp ON verification_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_enroll_exp ON enrollment_sessions(expires_at);
-- Use scheduled retention to purge expired enrollment/verification/session/throttle rows.
