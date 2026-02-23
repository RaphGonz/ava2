# Takedown Process — TAKE IT DOWN Act Compliance

**Version:** 1.0
**Effective Date:** 2026-02-23
**Review Cycle:** Quarterly or upon regulatory change

---

## 1. Scope

This process governs requests for removal of AI-generated images that allegedly:

- Depict an identifiable real person without consent (deepfake content)
- Violate intellectual property rights
- Contain illegal content under applicable law

**IMPORTANT NOTE:** The TAKE IT DOWN Act applies to deepfakes of real, identifiable people. Ava's core function is generating fictional characters from user descriptions — this process exists for **edge cases** only, such as:

- User uploads a real person's photo as avatar reference
- User manipulates the system to recreate a real individual's likeness
- Third-party reports content that may depict a real person

The vast majority of Ava-generated content consists of fictional characters and does not fall under TAKE IT DOWN Act requirements.

---

## 2. Timeline Summary

| Stage | Action | Deadline |
|-------|--------|----------|
| **Receipt** | Request received via email | Day 0 |
| **Acknowledgment** | Send confirmation with case ID | Within 24 hours |
| **Review** | Validate identity, verify content, assess claim | Within 48 hours of acknowledgment |
| **Action** | Remove content or send rejection notice | Within 48 hours of acknowledgment |
| **Total** | Full process from receipt to resolution | **72 hours maximum** |

---

## 3. Request Requirements

For a valid takedown request, the requestor must provide:

1. **Requestor Identity**
   - Full legal name
   - Contact email address
   - Phone number

2. **Proof of Identity**
   - Government-issued ID (if claiming to be the depicted individual)
   - Documentation establishing relationship to depicted individual (if requesting on another's behalf)

3. **Content Identification**
   - Direct URL to the content
   - OR unique image ID (if accessible)
   - Screenshot or copy of the content (if URL is expired or inaccessible)

4. **Statement of Non-Consent**
   - Clear statement that the depicted person did not consent to this use of their likeness
   - Description of how the image depicts a real, identifiable person (not a fictional character)

5. **Good Faith Statement**
   - Attestation that the information provided is accurate and made in good faith
   - Understanding of legal consequences for false claims

6. **Signature**
   - Electronic or written signature of the requestor

**Submission Email:** [takedown@ava-platform.com](mailto:takedown@ava-platform.com) (placeholder pending domain registration)

---

## 4. Review Process

### Step 1: Acknowledgment (Within 24 Hours)

- Log request in `takedown_requests` table (status = `received`)
- Generate unique case ID
- Send acknowledgment email to requestor with:
  - Case ID for tracking
  - Expected timeline (48 hours for review)
  - Contact information for follow-up
- Assign request to compliance reviewer
- Log event: `audit_log` entry with `event_type = 'takedown_request_received'`

### Step 2: Validation (Within 48 Hours)

**Identity Verification:**
- Verify requestor identity against provided documentation
- Confirm requestor has standing to make the request (depicted individual or authorized representative)

**Content Verification:**
- Locate content in system using URL, image ID, or screenshot
- Confirm content still exists and is accessible

**Claim Assessment:**
- **Valid Request:** Content depicts a real, identifiable person without consent
  - Evidence: facial recognition match to provided ID, social media verification, third-party confirmation
- **Invalid Request:** Content is a fictional character generated from user description
  - Evidence: generation logs show text-based prompt, no photo reference, character traits inconsistent with real person

**Update Status:** `status = 'reviewing'` in `takedown_requests` table

### Step 3: Action (Within 48 Hours of Acknowledgment)

#### If Request is VALID:

1. **Remove Content:**
   - Delete image from cloud storage (S3 or equivalent)
   - Purge all CDN cache entries
   - Revoke all authenticated access URLs
   - Mark image as deleted in database (do NOT fully delete record — retain metadata for audit trail)

2. **Log Removal:**
   - Update `takedown_requests` table: `status = 'completed'`, `action_taken = 'content_removed'`, `reviewed_at = NOW()`
   - Create `audit_log` entry: `event_type = 'takedown_content_removed'`, `resource_id = [image_id]`

3. **Notify Requestor:**
   - Send confirmation email with:
     - Action taken (content removed)
     - Timestamp of removal
     - Case closure notice
     - Counter-notice process (see Step 4)

4. **Notify Creator (User Who Generated Content):**
   - Send notification via platform messaging
   - Explanation: "Content removed due to valid takedown request"
   - Opportunity to submit counter-notice if they believe removal was in error

#### If Request is INVALID:

1. **Document Decision:**
   - Update `takedown_requests` table: `status = 'rejected'`, `notes = [explanation]`, `reviewed_at = NOW()`
   - Create `audit_log` entry: `event_type = 'takedown_review_completed'`, `result = 'rejected'`

2. **Notify Requestor:**
   - Send explanation email with:
     - Reason for rejection (e.g., "Content is AI-generated fictional character, not a real person")
     - Evidence supporting decision (without disclosing user PII)
     - Alternative options (if applicable, such as reporting ToS violations)

### Step 4: Counter-Notice (Optional)

If the content creator believes the takedown was invalid:

1. **Submission Requirements:**
   - Counter-notice must include: creator's identity, case ID, statement of good faith belief that removal was erroneous, consent to jurisdiction
   - Submitted to: [counter-notice@ava-platform.com](mailto:counter-notice@ava-platform.com)

2. **Review Timeline:**
   - Counter-notice reviewed within **10 business days**
   - Original requestor notified and given opportunity to respond (5 business days)

3. **Restoration Decision:**
   - If counter-notice is valid: restore content, notify both parties
   - If counter-notice is invalid: maintain removal, notify creator

4. **Audit Trail:**
   - All counter-notice activity logged in `audit_log` with `event_type = 'takedown_counter_notice_*'`

---

## 5. Audit Trail

All takedown activity is logged for compliance tracking. Relevant `audit_log` event types:

| Event Type | When Logged | Category |
|------------|-------------|----------|
| `takedown_request_received` | Request submitted via email | moderation |
| `takedown_review_started` | Reviewer assigned to case | moderation |
| `takedown_review_completed` | Validation/assessment finished | moderation |
| `takedown_content_removed` | Image deleted from storage | moderation |
| `takedown_counter_notice_received` | Creator submits counter-notice | moderation |
| `takedown_counter_notice_approved` | Content restored after valid counter-notice | moderation |

**Query Example (User Timeline):**
```sql
SELECT event_time, event_type, result, event_data
FROM audit_log
WHERE user_id = '[creator_user_id]'
  AND event_type LIKE 'takedown_%'
ORDER BY event_time DESC;
```

**Query Example (Active Requests):**
```sql
SELECT id, request_time, requestor_email, status, content_url
FROM takedown_requests
WHERE status IN ('received', 'reviewing')
  AND request_time > NOW() - INTERVAL '48 hours'
ORDER BY request_time ASC;
```

---

## 6. Escalation

### Law Enforcement Requests

If a takedown request originates from law enforcement or involves potential criminal activity (e.g., child exploitation, terrorism):

1. **Immediate Escalation:**
   - Forward request to legal counsel IMMEDIATELY
   - Do NOT delay response while awaiting legal advice
   - Preserve all content and metadata (do NOT delete)

2. **Timeline Exception:**
   - Standard 48-hour timeline may be extended with law enforcement coordination
   - Acknowledge request within 24 hours with explanation of legal review process

3. **Evidence Preservation:**
   - Create forensic copy of content and associated metadata
   - Log all access to evidence in `audit_log`
   - Maintain chain of custody documentation

### Regulatory Inquiries

For DMCA, GDPR, or other regulatory takedown demands:

- Consult legal counsel before taking action
- Document regulatory basis in `takedown_requests.notes`
- Ensure compliance with jurisdiction-specific timelines (may differ from standard 48-hour process)

---

## 7. Process Ownership

- **Process Owner:** Compliance Lead
- **Backup Reviewer:** Engineering Lead (for technical assessments)
- **Escalation Contact:** Legal Counsel
- **Review Frequency:** Quarterly or upon regulatory change

---

## 8. Updates & Amendments

This process may be updated to reflect:

- Changes to TAKE IT DOWN Act requirements
- New case law or regulatory guidance
- Platform-specific edge cases discovered in operation

All updates require:

1. Legal review
2. Notification to active users (if material change)
3. Version control (increment version number, add change log entry)

---

**Last Updated:** 2026-02-23
**Next Review:** 2026-05-23
