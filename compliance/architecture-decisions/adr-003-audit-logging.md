# ADR-003: Consolidated Audit Log Design

**Status:** Accepted
**Date:** 2026-02-23
**Related Documents:**
- compliance/audit-schema/schema.sql (to be created in separate task)
- compliance/policies/terms-of-service.md
- ADR-001 (Age Verification)
- ADR-002 (WhatsApp NSFW Image Delivery)

---

## Context

Compliance requirements for adult content platforms mandate tracking of specific events for regulatory audits, security monitoring, and legal defense:

**Required Tracking:**
- **Age verification:** When users verify age, what method was used, success/failure
- **Content moderation:** When content is blocked due to policy violations, which category triggered refusal
- **Image generation:** When NSFW images are generated, who requested them, what spice level, what model was used
- **Image access:** Who viewed which images, when, from what IP address (for security monitoring)
- **Account deletion:** When users exercise right to erasure, what data was deleted
- **Takedown requests:** When content is removed due to takedown request, who requested it, what was removed

**Regulatory Drivers:**
- **GDPR (EU):** Right to erasure requires proof of deletion
- **CCPA (California):** Data access requests require queryable audit logs
- **TAKE IT DOWN Act (Federal):** 48-hour takedown process requires timestamped audit trail
- **State age verification laws:** Audit logs demonstrate compliance with age verification requirements

**Technical Requirements:**
- Append-only log (no modification or deletion of audit records)
- Queryable by user ID, event type, date range, resource ID
- Flexible event data structure (different events have different metadata)
- Retention policy (2 years minimum, jurisdiction-specific extensions)
- Tamper-resistant (cannot be altered after creation)

## Decision

We implement a **single consolidated `audit_log` table** in PostgreSQL with JSONB `event_data` column for flexible event payloads. The table is append-only (enforced via database trigger) and partitioned by month for scalability.

### Schema Design

```sql
-- Core audit log table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(20) NOT NULL, -- 'auth', 'content', 'moderation', 'account'
    action VARCHAR(20) NOT NULL, -- 'create', 'read', 'update', 'delete', 'verify', 'block'
    resource_type VARCHAR(50), -- 'conversation', 'image', 'avatar', 'account'
    resource_id UUID,
    event_data JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    result VARCHAR(20) NOT NULL, -- 'success', 'failure', 'blocked'
    error_message TEXT
);
```

### Indexes for Performance

```sql
-- Primary indexes
CREATE INDEX idx_audit_log_event_time ON audit_log (event_time DESC);
CREATE INDEX idx_audit_log_user_id ON audit_log (user_id);
CREATE INDEX idx_audit_log_event_type ON audit_log (event_type);
CREATE INDEX idx_audit_log_category ON audit_log (event_category);
CREATE INDEX idx_audit_log_resource ON audit_log (resource_type, resource_id);

-- JSONB index for event_data queries
CREATE INDEX idx_audit_log_event_data_gin ON audit_log USING GIN (event_data);

-- Composite index for common compliance queries
CREATE INDEX idx_audit_log_user_time ON audit_log (user_id, event_time DESC);
```

### Append-Only Enforcement

```sql
-- Trigger protection: prevent direct modification of audit logs
CREATE OR REPLACE FUNCTION protect_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Direct modification of audit_log is forbidden';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_audit_modification
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION protect_audit_log();
```

**Effect:** Any attempt to `UPDATE` or `DELETE` rows from `audit_log` will raise an exception. The table is append-only—only `INSERT` is allowed.

### Partitioning Strategy (Future)

For high-volume systems, partition by month:

```sql
-- Create partitioned table
CREATE TABLE audit_log (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- ... (same columns as above)
) PARTITION BY RANGE (event_time);

-- Create partitions for each month
CREATE TABLE audit_log_2026_02 PARTITION OF audit_log
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE audit_log_2026_03 PARTITION OF audit_log
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Continue for each month...
```

**Note:** Partitioning is optional for Phase 1 (low volume). Add when audit log grows to >10M rows or query performance degrades.

### Event Categories and Examples

#### 1. Authentication Events (category: 'auth')

**Age Verification Attempt:**

```sql
INSERT INTO audit_log (user_id, event_type, event_category, action, result, event_data)
VALUES (
    'user-uuid',
    'age_verification',
    'auth',
    'verify',
    'success',
    '{"method": "self-declaration", "declared_age_18_plus": true, "version": 1}'::jsonb
);
```

**Login Attempt:**

```sql
INSERT INTO audit_log (user_id, event_type, event_category, action, result, ip_address, user_agent)
VALUES (
    'user-uuid',
    'login',
    'auth',
    'create',
    'success',
    '192.168.1.100',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
);
```

#### 2. Content Events (category: 'content')

**Image Generation:**

```sql
INSERT INTO audit_log (user_id, event_type, event_category, action, resource_type, resource_id, result, event_data)
VALUES (
    'user-uuid',
    'image_generation',
    'content',
    'create',
    'image',
    'image-uuid',
    'success',
    '{"model": "stable-diffusion-xl", "spice_level": "high", "prompt_hash": "abc123", "avatar_id": "avatar-uuid"}'::jsonb
);
```

**Image Access:**

```sql
INSERT INTO audit_log (user_id, event_type, event_category, action, resource_type, resource_id, result, ip_address, user_agent)
VALUES (
    'user-uuid',
    'image_access',
    'content',
    'read',
    'image',
    'image-uuid',
    'success',
    '192.168.1.100',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
);
```

#### 3. Moderation Events (category: 'moderation')

**Content Block (Policy Violation):**

```sql
INSERT INTO audit_log (user_id, event_type, event_category, action, resource_type, resource_id, result, event_data)
VALUES (
    'user-uuid',
    'content_block',
    'moderation',
    'block',
    'conversation',
    'conversation-uuid',
    'blocked',
    '{"trigger": "forbidden_category", "category": "non_consensual", "message_excerpt": "...", "confidence": 0.95}'::jsonb
);
```

**Takedown Request:**

```sql
INSERT INTO audit_log (user_id, event_type, event_category, action, resource_type, resource_id, result, event_data)
VALUES (
    'user-uuid',
    'takedown_request',
    'moderation',
    'delete',
    'image',
    'image-uuid',
    'success',
    '{"request_id": "takedown-uuid", "requestor_email": "example@example.com", "reason": "non-consensual depiction", "action_taken": "content_removed"}'::jsonb
);
```

#### 4. Account Events (category: 'account')

**Account Deletion (GDPR Right to Erasure):**

```sql
INSERT INTO audit_log (user_id, event_type, event_category, action, resource_type, result, event_data)
VALUES (
    'user-uuid',
    'account_deletion',
    'account',
    'delete',
    'account',
    'success',
    '{"deleted_conversations": 45, "deleted_images": 120, "deletion_requested_at": "2026-02-23T10:30:00Z"}'::jsonb
);
```

**Note:** After account deletion, audit logs are **anonymized** (user_id replaced with `deleted_user_{random_id}`). Events are retained for compliance but cannot be linked back to the deleted user.

### Data Minimization

**What We Log:**
- User ID (required for compliance queries)
- Event type, category, action (what happened)
- Resource type and ID (what was affected)
- Result (success, failure, blocked)
- Event-specific metadata in `event_data` JSONB (flexible per event type)

**What We Do NOT Log (Unless Required):**
- **Age verification:** No timestamp, no IP address, no device fingerprint (per user decision in CONTEXT.md)
- **Passwords or payment data:** Never logged in any event
- **Full message content:** Only excerpts (for moderation events) or hashes (for image prompts)
- **Unnecessary PII:** Email addresses, phone numbers, full names (only user_id as identifier)

**Exception:** IP address and user agent are logged for security-critical events (login, image access) to detect suspicious patterns.

### Retention Policy

**Minimum Retention:** 2 years (general best practice for audit logs)

**Jurisdiction-Specific Extensions:**
- **EU (GDPR):** No specific audit retention requirement, but 2 years recommended for legal defense
- **California (CCPA):** 12-month minimum for data access requests
- **Federal (TAKE IT DOWN Act):** No specified retention, but 48-hour response process implies recent data must be available

**Automated Cleanup:**

```sql
-- Delete audit logs older than 2 years
-- Run monthly via cron job
DELETE FROM audit_log
WHERE event_time < NOW() - INTERVAL '2 years';
```

**Note:** Account deletion events are retained even after 2 years (proof of GDPR compliance). Other events are purged after retention period.

### Querying Audit Logs

**Common Compliance Queries:**

```sql
-- Show all events for a specific user
SELECT * FROM audit_log
WHERE user_id = 'user-uuid'
ORDER BY event_time DESC;

-- Show all image generation events for a user
SELECT * FROM audit_log
WHERE user_id = 'user-uuid' AND event_type = 'image_generation'
ORDER BY event_time DESC;

-- Show all content blocks in the last 30 days
SELECT * FROM audit_log
WHERE event_category = 'moderation'
  AND result = 'blocked'
  AND event_time > NOW() - INTERVAL '30 days'
ORDER BY event_time DESC;

-- Show all age verification events
SELECT user_id, event_time, event_data->>'method' AS method, result
FROM audit_log
WHERE event_type = 'age_verification'
ORDER BY event_time DESC;

-- Query JSONB event_data (e.g., find all high spice level image generations)
SELECT * FROM audit_log
WHERE event_type = 'image_generation'
  AND event_data->>'spice_level' = 'high'
ORDER BY event_time DESC;
```

**GIN Index Performance:** The `idx_audit_log_event_data_gin` index enables fast queries on JSONB fields (e.g., `event_data->>'spice_level'`).

## Consequences

### Positive

1. **Single Table Simplifies Compliance:** All audit events in one table with consistent schema. Compliance queries (e.g., "show all events for user X") are straightforward.

2. **JSONB Flexibility:** Different event types have different metadata. JSONB allows flexible event payloads without altering schema for each new event type.

3. **Append-Only Integrity:** Database trigger ensures audit logs cannot be modified or deleted. Tamper-resistant for regulatory audits.

4. **Queryable with SQL:** PostgreSQL's full SQL support enables complex compliance queries (joins, aggregations, date filters). No need for log parsing tools.

5. **Scalable with Partitioning:** Monthly partitions allow high-volume systems to manage audit log size. Old partitions can be archived to cold storage.

6. **GDPR-Compliant Anonymization:** Account deletion anonymizes audit logs (user_id replaced) rather than deleting them. Retains compliance evidence without PII.

### Negative

1. **Single Table May Not Scale to Billions of Rows:** If audit volume grows extremely large (millions of events per day), single table queries may slow down.

   **Mitigation:** Partitioning by month (see schema above). Old partitions archived to cold storage (AWS Glacier, Cloudflare R2). For Phase 1-7, single table with partitioning is sufficient.

2. **GIN Index on JSONB Has Storage Overhead:** GIN indexes on JSONB columns are larger than standard B-tree indexes. May increase storage costs.

   **Mitigation:** GIN index is critical for event_data queries. Storage cost is acceptable compared to query performance benefits.

3. **Append-Only Means Errors Cannot Be Corrected:** If a log entry is inserted with incorrect data, it cannot be updated or deleted.

   **Mitigation:** Insert a corrective event (e.g., `event_type: 'audit_correction'`) that references the incorrect entry. Original entry remains, but correction is documented.

4. **Retention Policy Requires Manual Deletion:** PostgreSQL does not auto-delete old partitions. Requires cron job or scheduled task.

   **Mitigation:** Automated cleanup script runs monthly. Partitions older than 2 years are dropped. Low operational burden.

## Alternatives Considered

### Alternative 1: Separate Tables Per Event Type

**Approach:** Create `age_verification_log`, `image_generation_log`, `content_moderation_log`, etc.

**Rejected Because:**
- **Query complexity:** Compliance queries (e.g., "show all events for user X") require UNION across multiple tables
- **Schema maintenance:** Adding new event types requires new tables
- **No performance benefit:** Single table with indexes performs similarly to multiple tables

### Alternative 2: Application Log Files (JSON, Plain Text)

**Approach:** Write audit events to log files (e.g., `audit.log`, `moderation.log`) instead of database.

**Rejected Because:**
- **Not queryable:** Log files require parsing tools (grep, awk, log aggregators) for compliance queries
- **No integrity guarantees:** Files can be modified or deleted without detection
- **No indexing:** Searching large log files is slow
- **GDPR compliance difficult:** Anonymizing user_id in account deletion requires rewriting entire log file

### Alternative 3: Time-Series Database (InfluxDB, TimescaleDB)

**Approach:** Use time-series DB optimized for append-only event data.

**Rejected Because:**
- **Adds infrastructure complexity:** Requires separate database service
- **PostgreSQL with partitioning is sufficient:** For Phase 1-7 volume, PostgreSQL performs well
- **SQL compatibility:** PostgreSQL offers full SQL support; time-series DBs have limited query capabilities

### Alternative 4: External Audit Service (Splunk, Datadog, AWS CloudWatch Logs)

**Approach:** Send audit events to external logging/monitoring service.

**Rejected Because:**
- **Cost:** External services charge per GB ingested; audit logs are high-volume
- **Data residency:** Sensitive audit data (user_id, IP addresses) stored with third party
- **Compliance risk:** GDPR requires control over audit data; external services may not meet requirements
- **PostgreSQL is sufficient:** In-house database provides control, cost savings, and compliance flexibility

**Note:** External services may be used for **application logs** (errors, performance metrics) but not **audit logs** (compliance-critical events).

## Implementation Notes

- **Phase 1:** Create audit_log schema, indexes, and append-only trigger. Document event types.
- **Phase 2+:** Implement audit logging in application code (age verification, login, image generation).
- **Phase 6:** Add image access logging when web portal is built.
- **Phase 7:** Add image generation audit logging when image generation is implemented.

**Database Migration:** Schema will be created in `compliance/audit-schema/schema.sql` and applied via migration script in Phase 2.

## Related Decisions

- **ADR-001 (Age Verification):** Age verification events logged in `audit_log` with minimal data (user_id, method, result). No timestamp or IP address.
- **ADR-002 (WhatsApp NSFW):** Image access events logged in `audit_log` with user_id, image_id, IP address, and user agent.
- **Terms of Service:** Account deletion policy requires audit log anonymization (user_id replaced with anonymized token).

---

**Last Updated:** 2026-02-23
