-- =============================================================================
-- Ava Platform - Audit Log Performance Indexes
-- =============================================================================
-- Purpose: Optimize common compliance query patterns
-- Database: PostgreSQL 14+
-- Author: Claude Code
-- Created: 2026-02-23
-- =============================================================================

-- -----------------------------------------------------------------------------
-- audit_log indexes
-- -----------------------------------------------------------------------------

-- Temporal queries (most recent events)
CREATE INDEX idx_audit_log_event_time ON audit_log (event_time DESC);

-- User-specific audit trail
CREATE INDEX idx_audit_log_user_id ON audit_log (user_id);

-- Event type filtering
CREATE INDEX idx_audit_log_event_type ON audit_log (event_type);

-- Category-based queries
CREATE INDEX idx_audit_log_category ON audit_log (event_category);

-- Resource lookups
CREATE INDEX idx_audit_log_resource ON audit_log (resource_type, resource_id);

-- JSONB content search (GIN index for fast JSON queries)
CREATE INDEX idx_audit_log_event_data_gin ON audit_log USING GIN (event_data);

-- Composite index for most common query: user timeline
-- Optimizes: SELECT * FROM audit_log WHERE user_id = ? ORDER BY event_time DESC
CREATE INDEX idx_audit_log_user_time ON audit_log (user_id, event_time DESC);

-- -----------------------------------------------------------------------------
-- takedown_requests indexes
-- -----------------------------------------------------------------------------

-- Status filtering (active requests)
CREATE INDEX idx_takedown_requests_status ON takedown_requests (status);

-- Temporal queries (pending requests by age)
CREATE INDEX idx_takedown_requests_request_time ON takedown_requests (request_time DESC);

-- -----------------------------------------------------------------------------
-- Index documentation
-- -----------------------------------------------------------------------------
COMMENT ON INDEX idx_audit_log_event_time IS 'Supports chronological queries for recent audit events.';
COMMENT ON INDEX idx_audit_log_user_time IS 'Composite index optimized for user-specific audit trail queries with time ordering.';
COMMENT ON INDEX idx_audit_log_event_data_gin IS 'GIN index enables fast JSONB queries on event_data for compliance searches.';
COMMENT ON INDEX idx_takedown_requests_status IS 'Supports filtering active takedown requests (received, reviewing) for workflow dashboards.';
