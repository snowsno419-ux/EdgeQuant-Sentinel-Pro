-- Phase 7B2A: future separate market/position DEMO opt-ins; DEFAULT OFF.
-- No automatic dispatch / lease is created by this schema migration.
ALTER TABLE copy_subscriptions ADD COLUMN IF NOT EXISTS demo_market_copy_enabled BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE copy_subscriptions ADD COLUMN IF NOT EXISTS demo_position_actions_enabled BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE copy_subscriptions ADD COLUMN IF NOT EXISTS demo_max_spread_points INTEGER NOT NULL DEFAULT 40;
ALTER TABLE copy_subscriptions ADD COLUMN IF NOT EXISTS demo_max_deviation_points INTEGER NOT NULL DEFAULT 20;
ALTER TABLE copy_subscriptions DROP CONSTRAINT IF EXISTS copy_demo_max_spread_range;
ALTER TABLE copy_subscriptions ADD CONSTRAINT copy_demo_max_spread_range CHECK(demo_max_spread_points BETWEEN 1 AND 500);
ALTER TABLE copy_subscriptions DROP CONSTRAINT IF EXISTS copy_demo_max_deviation_range;
ALTER TABLE copy_subscriptions ADD CONSTRAINT copy_demo_max_deviation_range CHECK(demo_max_deviation_points BETWEEN 1 AND 500);
