-- Phase 2: account identity + tenant isolation; NO broker passwords stored.
CREATE TABLE IF NOT EXISTS tenants (
 id UUID PRIMARY KEY, name VARCHAR(80) NOT NULL,
 kind VARCHAR(16) NOT NULL CHECK(kind IN ('RECEIVER','PROVIDER','OWNER')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS users (
 id UUID PRIMARY KEY, tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
 email VARCHAR(254) NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 role VARCHAR(16) NOT NULL CHECK(role IN ('RECEIVER','PROVIDER','OWNER')),
 verified_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_tenant ON users(tenant_id);
CREATE TABLE IF NOT EXISTS email_verifications (
 user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 token_hash CHAR(64) NOT NULL UNIQUE,
 expires_at TIMESTAMPTZ NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
 id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
 token_hash CHAR(64) NOT NULL UNIQUE,
 expires_at TIMESTAMPTZ NOT NULL,
 revoked_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id);
CREATE TABLE IF NOT EXISTS broker_accounts (
 id UUID PRIMARY KEY, tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
 server VARCHAR(100) NOT NULL, login VARCHAR(20) NOT NULL,
 label VARCHAR(80) NOT NULL DEFAULT '', is_main BOOLEAN NOT NULL DEFAULT false,
 pairing_status VARCHAR(16) NOT NULL DEFAULT 'UNPAIRED'
  CHECK(pairing_status IN ('UNPAIRED','PAIRING','CONNECTED','DISCONNECTED','ERROR')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(tenant_id,server,login)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_broker_main_tenant ON broker_accounts(tenant_id) WHERE is_main = true;
CREATE INDEX IF NOT EXISTS ix_brokers_tenant ON broker_accounts(tenant_id);
CREATE TABLE IF NOT EXISTS audit_events (
 id UUID PRIMARY KEY, tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
 actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
 event_type VARCHAR(64) NOT NULL, object_id VARCHAR(100),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_audit_tenant ON audit_events(tenant_id, created_at DESC);
