-- =============================================================================
-- Ava Platform - Audit Log and Takedown Request Schema
-- =============================================================================
-- Purpose: Core compliance and audit trail infrastructure
-- Database: PostgreSQL 14+
-- Author: Claude Code
-- Created: 2026-02-23
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: audit_log
-- Purpose: Immutable audit trail for compliance tracking
-- -----------------------------------------------------------------------------
CREATE TABLE audit_log (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Temporal
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Actor
    user_id UUID NOT NULL,

    -- Event classification
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(20) NOT NULL CHECK (event_category IN ('auth', 'content', 'moderation', 'account')),
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'read', 'update', 'delete', 'verify', 'block')),

    -- Resource reference
    resource_type VARCHAR(50),
    resource_id UUID,

    -- Event payload
    event_data JSONB NOT NULL DEFAULT '{}',

    -- Context
    ip_address INET,
    user_agent TEXT,
    session_id UUID,

    -- Outcome
    result VARCHAR(20) NOT NULL CHECK (result IN ('success', 'failure', 'blocked')),
    error_message TEXT
);

-- -----------------------------------------------------------------------------
-- Table: takedown_requests
-- Purpose: TAKE IT DOWN Act compliance tracking
-- -----------------------------------------------------------------------------
CREATE TABLE takedown_requests (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Temporal
    request_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Requestor information
    requestor_email VARCHAR(255) NOT NULL,
    requestor_name VARCHAR(255),

    -- Content identification
    content_url TEXT NOT NULL,
    content_id UUID,
    reason TEXT NOT NULL,

    -- Processing status
    status VARCHAR(20) NOT NULL CHECK (status IN ('received', 'reviewing', 'completed', 'rejected')),
    action_taken VARCHAR(50),

    -- Review tracking
    reviewer_id UUID,
    reviewed_at TIMESTAMPTZ,
    notes TEXT
);

-- -----------------------------------------------------------------------------
-- Trigger: Protect audit_log from modification
-- Purpose: Ensure append-only audit trail (compliance requirement)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION protect_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Direct modification of audit_log is forbidden';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_protect_update
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW
EXECUTE FUNCTION protect_audit_log();

-- -----------------------------------------------------------------------------
-- Comments for documentation
-- -----------------------------------------------------------------------------
COMMENT ON TABLE audit_log IS 'Append-only audit trail for compliance tracking. Protected from UPDATE/DELETE by trigger.';
COMMENT ON TABLE takedown_requests IS 'TAKE IT DOWN Act compliance: tracks content removal requests with 48-hour review timeline.';
COMMENT ON COLUMN audit_log.event_data IS 'Flexible JSONB storage for event-specific metadata. No PII stored here per data minimization policy.';
COMMENT ON COLUMN audit_log.event_category IS 'Coarse categorization: auth (login/logout), content (creation), moderation (blocking), account (deletion).';
COMMENT ON COLUMN takedown_requests.status IS 'received = acknowledged, reviewing = under investigation, completed = removed, rejected = invalid request.';
