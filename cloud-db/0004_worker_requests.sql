-- User requests for managed DEMO Windows workers. Requests do NOT provision/launch terminals.
CREATE TABLE IF NOT EXISTS worker_provision_requests (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 broker_id TEXT NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
 state TEXT NOT NULL CHECK(state IN('PENDING','APPROVED','PROVISIONING','CONNECTED','FAILED','CANCELLED')) DEFAULT 'PENDING',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(user_id,broker_id)
);
CREATE INDEX IF NOT EXISTS idx_worker_request_user ON worker_provision_requests(user_id,created_at DESC);
-- Only an authorized human/operator may assign public Ed25519 worker keys and change state.
