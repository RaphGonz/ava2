# Phase 1: Foundation & Compliance - Research

**Researched:** 2026-02-23
**Domain:** Legal compliance, content moderation, age verification, and audit infrastructure for AI-generated NSFW content platforms
**Confidence:** MEDIUM

## Summary

Phase 1 establishes the legal and compliance foundation for an AI companion platform that offers NSFW features. The primary challenge is navigating an evolving regulatory landscape (2026 age verification laws, TAKE IT DOWN Act, state-level adult content regulations) while architecting for future adaptability. The phase focuses on documentation and database schema design rather than full implementation.

**Key insight:** Self-declaration age verification (checkbox only) is increasingly insufficient for 2026 compliance standards. While the user has chosen this approach for MVP, the architecture MUST be pluggable to accommodate ID verification, biometric scanning, or third-party verification services when regulations tighten.

**Primary recommendation:** Treat all decisions in this phase as "compliance framework blueprints" rather than implemented systems. The deliverables are ToS documents, policy documentation, database schemas, and architectural decision records—not production code. The audit log schema should be built and tested, but enforcement logic and takedown workflows remain documentation-only until Phase 2+.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Age Verification:**
- One-time self-declaration checkbox at signup ("I am 18+")
- No stored proof of declaration for now (no timestamp/IP logging)
- Declining the declaration = no access to the app at all (not even secretary mode)
- Implicit secondary signals: phone account ownership, payment card on file
- No full ID verification unless regulations require it later
- Architecture must include a pluggable verification slot — new verification methods (ID check, biometric, etc.) can be added without rearchitecting

**Content Policy — Forbidden Categories:**
- Absolutely forbidden, enforced at system level:
  - Minors in any sexual context
  - Non-consensual scenarios (rape fantasy, coercion roleplay)
  - Incest scenarios
  - Violence combined with sexual content
  - Bestiality
  - Torture
- Refusal is a system-level message (red box), not in-character — breaks the persona to make the boundary clear
- No lockout or escalation on refusal — flat refusal each time
- User bears legal responsibility if they jailbreak past guardrails

**Content Escalation & Spice Control:**
- User-accessible "spice level" setting in settings (simple tiers: e.g., low/medium/high/max)
- Spice level is primarily inferred from conversation tone — the setting exists for users who want manual control
- The setting acts as both floor (accelerate if user can't flirt) and ceiling (cap if user wants to keep things mild)
- Bot proactively escalates — all personality presets initiate escalation on their own
- Escalation pace is driven by the personality preset: shy = slow, dominant = fast, but all move forward
- "Stop" safe word exits intimate mode and lowers spice one notch (does not reset to zero)
- Next intimate session resumes at the lowered spice level

**Secretary Mode Boundaries:**
- Secretary mode is strictly professional — hard wall, no exceptions
- If user tries to flirt in secretary mode: playful deflection ("shh not now") but refuses to engage further
- No romantic or sexual content leaks into secretary responses

**Compliance Framework:**
- General best-practice compliance for now — no specific framework (GDPR, CCPA) until commercializing in specific regions
- TAKE IT DOWN Act: not applicable — all images are AI-generated fictional characters, not real people
- Watermarking and C2PA credentials: documented as future requirement (implemented in Phase 7), not built in Phase 1
- Basic audit log database schema built in Phase 1 — logs conversation events and image generation requests
- Full self-service account deletion: user can wipe all data (account, conversations, generated images) — immediate and irreversible

### Claude's Discretion
- Specific audit log schema design (tables, columns, indexes)
- ToS document structure and legal language
- Exact wording of age declaration checkbox
- System refusal message design and copy
- How to structure the pluggable verification architecture documentation

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SAFE-01 | Age verification enforces 20+ floor on avatar creation — no exceptions | Self-declaration architecture (§ Standard Stack), pluggable verification pattern (§ Architecture Patterns), regulatory context (§ State of the Art) |
| SAFE-02 | Content guardrails prevent generation of non-consensual or illegal content | Content moderation patterns (§ Architecture Patterns), enforcement mechanisms (§ Code Examples), system refusal design (§ Architecture Patterns) |
| SAFE-03 | System complies with TAKE IT DOWN Act requirements (48-hour takedown process) | 48-hour takedown process (§ Common Pitfalls), TAKE IT DOWN Act scope (§ Don't Hand-Roll), process documentation (§ Code Examples) |
| PLAT-03 | NSFW photos on WhatsApp are delivered via secure authenticated web links (not inline) | WhatsApp Business API restrictions (§ Common Pitfalls), web portal architecture (§ Architecture Patterns) |
| ARCH-04 | Cloud-hosted on VPS/AWS, always-on for message handling | General infrastructure requirement — no specific research needed for Phase 1 compliance work |

</phase_requirements>

## Standard Stack

### Core Legal & Compliance Tools

| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| Attorney review | N/A | ToS/legal framework validation | Essential for adult content platforms — generic templates are insufficient; specialized legal counsel experienced in adult content regulation is mandatory |
| PostgreSQL | 17+ | Audit log database | JSON handling improvements in v17 make it ideal for flexible audit schemas; JSONB storage handles any table structure without schema changes |
| C2PA (future) | 2.1+ | Content credentials for AI images | Industry standard for AI-generated content provenance; combines metadata with digital watermarks that survive social media uploads and resist cropping/rotation |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| bcrypt | Latest | Password hashing | Standard for user authentication systems |
| uuid | Latest | Generating unique identifiers | For audit log entries, user IDs, session tokens |
| pg (node-postgres) | Latest | PostgreSQL client for Node.js | If building audit system in Node.js backend |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PostgreSQL | MongoDB | PostgreSQL's structured audit logs with JSONB flexibility offer better compliance querying; MongoDB's schemaless nature makes regulatory audits harder |
| Attorney review | Online ToS generators | Generates legally inadequate documents for adult content platforms; legal liability risk far exceeds cost savings |
| Self-hosted storage | Cloud object storage (S3, Cloudflare R2) | Self-hosted increases compliance burden (data residency, backups, GDPR erasure); cloud providers offer compliance-certified storage |

**Installation:**
```bash
# PostgreSQL (platform-specific)
# Windows: Download installer from postgresql.org
# Linux: apt-get install postgresql-17
# macOS: brew install postgresql@17

# Node.js PostgreSQL client
npm install pg uuid bcrypt
```

## Architecture Patterns

### Recommended Project Structure

```
compliance/
├── policies/
│   ├── terms-of-service.md         # ToS document
│   ├── content-policy.md           # Forbidden categories, enforcement
│   ├── takedown-process.md         # 48-hour process documentation
│   └── age-verification-strategy.md # Current + pluggable future
├── audit-schema/
│   ├── schema.sql                  # PostgreSQL audit tables
│   ├── indexes.sql                 # Performance indexes
│   └── migration-001.sql           # Initial schema migration
└── architecture-decisions/
    ├── adr-001-age-verification.md # Pluggable verification architecture
    ├── adr-002-whatsapp-nsfw.md    # Text-only + web portal decision
    └── adr-003-audit-logging.md    # Audit log design rationale
```

### Pattern 1: Pluggable Age Verification

**What:** An abstraction layer that allows swapping age verification methods without rearchitecting the application.

**When to use:** When regulatory requirements are evolving and current solution (self-declaration) may need upgrading to ID verification, biometrics, or third-party services.

**Architecture:**

```typescript
// Verification provider interface
interface AgeVerificationProvider {
  verify(userId: string, data: VerificationData): Promise<VerificationResult>;
  requiresReVerification(): boolean;
  getSessionDuration(): number; // minutes
}

// Self-declaration provider (Phase 1)
class SelfDeclarationProvider implements AgeVerificationProvider {
  async verify(userId: string, data: { declaredAge18Plus: boolean }): Promise<VerificationResult> {
    return {
      verified: data.declaredAge18Plus,
      method: 'self-declaration',
      timestamp: new Date(),
      requiresReVerification: false
    };
  }

  requiresReVerification(): boolean { return false; }
  getSessionDuration(): number { return Infinity; }
}

// Future ID verification provider (Phase 2+)
class IDVerificationProvider implements AgeVerificationProvider {
  async verify(userId: string, data: { idDocument: File, selfie: File }): Promise<VerificationResult> {
    // Third-party verification API call
    // Returns: verified, confidence level, PII handling
  }

  requiresReVerification(): boolean { return true; }
  getSessionDuration(): number { return 60; } // Re-verify every 60 minutes
}

// Verification manager
class AgeVerificationManager {
  private provider: AgeVerificationProvider;

  constructor(provider: AgeVerificationProvider) {
    this.provider = provider;
  }

  setProvider(provider: AgeVerificationProvider): void {
    this.provider = provider;
  }

  async verifyAge(userId: string, data: VerificationData): Promise<VerificationResult> {
    const result = await this.provider.verify(userId, data);

    // Log verification attempt (audit trail)
    await auditLog.record({
      event: 'age_verification_attempt',
      userId,
      method: result.method,
      verified: result.verified,
      timestamp: result.timestamp
    });

    return result;
  }
}
```

**Key principle:** The application code calls `AgeVerificationManager.verifyAge()` everywhere. Swapping providers is a configuration change, not a code rewrite.

### Pattern 2: Audit Log Schema (PostgreSQL)

**What:** A single, consolidated audit log table that captures all compliance-relevant events using JSONB for flexible event data.

**When to use:** For GDPR/CCPA compliance, security monitoring, takedown process documentation, and regulatory audits.

**Schema design:**

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

-- Performance indexes
CREATE INDEX idx_audit_log_event_time ON audit_log (event_time DESC);
CREATE INDEX idx_audit_log_user_id ON audit_log (user_id);
CREATE INDEX idx_audit_log_event_type ON audit_log (event_type);
CREATE INDEX idx_audit_log_category ON audit_log (event_category);
CREATE INDEX idx_audit_log_resource ON audit_log (resource_type, resource_id);
CREATE INDEX idx_audit_log_event_data_gin ON audit_log USING GIN (event_data);

-- Composite index for common compliance queries
CREATE INDEX idx_audit_log_user_time ON audit_log (user_id, event_time DESC);

-- Partition by month for high-volume systems
CREATE TABLE audit_log_2026_02 PARTITION OF audit_log
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

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

**Example audit events:**

```sql
-- Age verification attempt
INSERT INTO audit_log (user_id, event_type, event_category, action, result, event_data)
VALUES (
    'user-uuid',
    'age_verification',
    'auth',
    'verify',
    'success',
    '{"method": "self-declaration", "declared_age_18_plus": true, "version": 1}'::jsonb
);

-- Content moderation block
INSERT INTO audit_log (user_id, event_type, event_category, action, resource_type, resource_id, result, event_data)
VALUES (
    'user-uuid',
    'content_block',
    'moderation',
    'block',
    'conversation',
    'conversation-uuid',
    'blocked',
    '{"trigger": "forbidden_category", "category": "non_consensual", "message_excerpt": "..."}'::jsonb
);

-- Image generation request
INSERT INTO audit_log (user_id, event_type, event_category, action, resource_type, resource_id, result, event_data)
VALUES (
    'user-uuid',
    'image_generation',
    'content',
    'create',
    'image',
    'image-uuid',
    'success',
    '{"model": "stable-diffusion", "spice_level": "medium", "prompt_hash": "abc123"}'::jsonb
);

-- Account deletion (GDPR right to erasure)
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

**Retention policy:**

```sql
-- Delete audit logs older than 2 years (or jurisdiction-specific requirement)
DELETE FROM audit_log
WHERE event_time < NOW() - INTERVAL '2 years';
```

**Exclusion strategy:** Never log sensitive data (passwords, payment details, PII beyond user_id). For compliance queries, log only what's required.

### Pattern 3: System Refusal Message Design

**What:** Clear, non-persona system messages that enforce content boundaries without punishing users.

**When to use:** When content guardrails detect forbidden categories (minors, non-consent, violence, etc.).

**Design principles:**
1. **Break the persona:** Use a visually distinct system message (red box, different typography) to signal this is a platform boundary, not character behavior
2. **Transparent explanation:** Tell the user why the request was blocked, referencing the specific policy
3. **No escalation:** Flat refusal every time — no lockouts, no "strikes"
4. **User responsibility:** Remind user they bear legal responsibility if they circumvent guardrails

**Example refusal UI:**

```
╔═══════════════════════════════════════════════════════════╗
║  ⚠️  CONTENT POLICY VIOLATION                             ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Your request was blocked because it violates our         ║
║  content policy (non-consensual scenarios).               ║
║                                                           ║
║  We cannot generate content involving:                    ║
║  • Non-consensual scenarios                               ║
║  • Minors in sexual contexts                              ║
║  • Violence combined with sexual content                  ║
║  • [See full policy: /content-policy]                     ║
║                                                           ║
║  You may rephrase your request. Repeated attempts to      ║
║  circumvent these guardrails are your legal               ║
║  responsibility.                                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

**Copy guidelines:**
- **Tone:** Firm but not punitive. "We cannot" not "You are not allowed"
- **Brevity:** 2-3 sentences max. Link to full policy for details
- **Specificity:** Name the violated category, don't be vague ("inappropriate content")
- **No judgment:** Avoid moralistic language ("disgusting," "wrong")

**Secretary mode deflection (different pattern):**

Secretary mode uses playful in-character deflection, not system refusals:

```
User: "You're so beautiful"
Bot: "Shh, not now 😊 We're in work mode. Need me to help with anything else?"
```

Key difference: Secretary deflection is light and in-character. Content policy refusals are system-level and break immersion.

### Pattern 4: WhatsApp NSFW Image Delivery Architecture

**What:** Text-only intimate conversations on WhatsApp with NSFW images delivered via secure, authenticated web portal links.

**Why:** WhatsApp Business API explicitly prohibits sexually explicit materials or nudity in messages. Violation results in account suspension, message throttling, or permanent ban.

**Architecture:**

```
[User] <--WhatsApp--> [Bot Backend]
                           |
                           | Generate image
                           v
                      [Image Storage]
                      (S3 / R2 / CDN)
                           |
                           | Upload + create signed URL
                           v
                     [Web Portal Auth]
                     (JWT token in URL)
                           |
                           | Return secure link
                           v
[User] <--WhatsApp--> "Your photo is ready: https://ava-portal.com/i/{token}"
                           |
                           | Click link
                           v
                    [Web Portal: Image Viewer]
                    (Full-screen NSFW image display)
```

**Key components:**

1. **Image generation:** Backend generates image via API (Stable Diffusion, Midjourney, etc.)
2. **Secure storage:** Upload to cloud storage (S3, Cloudflare R2) with private access only
3. **Signed URL generation:** Create time-limited, user-specific JWT token
4. **WhatsApp message:** Send text message with HTTPS link to web portal
5. **Web portal authentication:** Verify JWT token, confirm user identity, serve image
6. **Token expiration:** Default 24-hour expiration; user can regenerate link

**Security considerations:**
- JWT tokens must be single-use or short-lived (24 hours)
- Rate limit link generation to prevent abuse
- Log all image access attempts (audit trail)
- HTTPS only (no unencrypted image URLs)

**User experience:**
- "Your photo is ready! Tap to view: [link]"
- Link opens in-app browser or external browser
- Full-screen image display with download option
- "Generate another" button returns to WhatsApp chat

### Pattern 5: Content Policy Enforcement (LLM Guardrails)

**What:** Real-time content detection that analyzes user messages and bot responses before delivery, blocking forbidden categories.

**Implementation layers:**

1. **Prompt analysis:** Scan user input for policy violations before sending to LLM
2. **Response analysis:** Scan bot output before sending to user
3. **Classification API:** Use content safety API (OpenAI Moderation, Azure Content Safety, Anthropic Claude safety classifiers)

**Example flow:**

```typescript
async function handleUserMessage(userId: string, message: string): Promise<BotResponse> {
  // Layer 1: Analyze user input
  const userAnalysis = await contentSafety.analyze(message);

  if (userAnalysis.violatesPolicy) {
    await auditLog.record({
      event: 'content_block',
      userId,
      trigger: 'user_input',
      category: userAnalysis.category, // e.g., 'non_consensual'
      result: 'blocked'
    });

    return {
      type: 'system_refusal',
      message: getRefusalMessage(userAnalysis.category)
    };
  }

  // Layer 2: Generate bot response
  const botResponse = await llm.generateResponse(userId, message);

  // Layer 3: Analyze bot output
  const botAnalysis = await contentSafety.analyze(botResponse);

  if (botAnalysis.violatesPolicy) {
    await auditLog.record({
      event: 'content_block',
      userId,
      trigger: 'bot_output',
      category: botAnalysis.category,
      result: 'blocked'
    });

    // Regenerate with stricter system prompt
    return await llm.generateResponse(userId, message, { safetyLevel: 'strict' });
  }

  return {
    type: 'bot_message',
    message: botResponse
  };
}
```

**Content safety classification:**

```typescript
interface ContentSafetyResult {
  violatesPolicy: boolean;
  category: 'minors' | 'non_consensual' | 'incest' | 'violence_sexual' | 'bestiality' | 'torture' | null;
  confidence: number; // 0.0 to 1.0
  explanation: string;
}

// Example: OpenAI Moderation API
async function analyzeContent(text: string): Promise<ContentSafetyResult> {
  const response = await openai.moderations.create({ input: text });
  const result = response.results[0];

  // Map OpenAI categories to internal policy categories
  if (result.categories.sexual_minors || result.categories.child_abuse) {
    return { violatesPolicy: true, category: 'minors', confidence: 0.95, explanation: 'Minor detected' };
  }

  if (result.categories.violence && result.categories.sexual) {
    return { violatesPolicy: true, category: 'violence_sexual', confidence: 0.90, explanation: 'Violence + sexual content' };
  }

  // Non-consensual detection requires custom classifier (keyword + semantic analysis)
  const nonConsensualSignals = detectNonConsensual(text);
  if (nonConsensualSignals.detected) {
    return { violatesPolicy: true, category: 'non_consensual', confidence: nonConsensualSignals.confidence, explanation: 'Non-consensual scenario detected' };
  }

  return { violatesPolicy: false, category: null, confidence: 0, explanation: 'Content passes policy' };
}
```

**Note:** Off-the-shelf moderation APIs (OpenAI, Azure) handle minors, violence, and sexual content well. Custom classifiers are needed for incest, non-consent detection, and bestiality (semantic analysis, keyword matching).

### Anti-Patterns to Avoid

- **Don't store PII in audit logs:** Log user_id only, not names, emails, or addresses. GDPR requires minimal data collection.
- **Don't use generic ToS templates:** Adult content platforms require specialized legal review. Generic templates expose you to liability.
- **Don't lock users out on refusal:** Flat refusal every time, no escalation. Lockouts create user frustration and support burden.
- **Don't log passwords or payment data:** Never log sensitive authentication credentials or financial information in audit tables.
- **Don't make age verification "verify once, trust forever" without pluggable architecture:** Regulations are tightening — build for future ID verification now.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Content moderation for minors/violence | Custom keyword filters | OpenAI Moderation API, Azure Content Safety, Claude safety classifiers | Edge cases are deceptively complex: "18-year-old schoolgirl" vs "18-year-old university student" requires semantic analysis beyond keyword matching. Commercial APIs have massive training datasets and ongoing updates. |
| Age verification (future phases) | Custom ID verification | Onfido, Veriff, Jumio, Stripe Identity | ID forgery detection, liveness checks, global ID document recognition require specialized computer vision. Legal liability if verification fails and minors access content. |
| Data deletion (GDPR right to erasure) | Manual SQL scripts | Structured deletion workflows + audit trails | Incomplete deletion (missing backup databases, cached images, CDN copies) creates GDPR liability. Audit trail of deletion required for regulatory proof. |
| ToS/legal documents | Online generators or copying competitors | Attorney specializing in adult content platforms | Section 2257 compliance (if user-generated content added later), state-specific age verification laws, liability waivers for AI-generated content require expert review. Generic templates miss jurisdiction-specific requirements. |
| C2PA watermarking (Phase 7) | Custom watermarking | Digimarc, C2PA SDK, Adobe Content Authenticity Initiative tools | Watermarks must survive cropping, resizing, social media uploads, and re-encoding. C2PA 2.1 combines metadata with imperceptible digital watermarks — implementing this correctly requires specialized expertise. |

**Key insight:** Compliance and safety problems have hidden complexity. "Just check if the message contains 'minor'" fails on euphemisms, misspellings, context-dependent language, and jailbreak prompts. Use commercial APIs for safety-critical systems.

## Common Pitfalls

### Pitfall 1: Treating Self-Declaration as Permanent Solution

**What goes wrong:** Building age verification as a hardcoded checkbox without abstraction layer. When regulations require ID verification (likely within 12-18 months), requires full rewrite.

**Why it happens:** Self-declaration is simplest implementation. Developers don't anticipate regulatory changes.

**How to avoid:**
- Implement pluggable verification architecture from day one (see Pattern 1)
- All verification checks call `AgeVerificationManager.verifyAge()`, never check flags directly
- Configuration file specifies active provider: `ageVerificationProvider: 'self-declaration'`
- Document upgrade path: "To enable ID verification, implement `IDVerificationProvider` and change config to `'id-verification'`"

**Warning signs:**
- Direct checks like `if (user.agreedToTerms)` scattered throughout codebase
- Age verification logic embedded in signup flow without abstraction
- No documentation of future verification methods

### Pitfall 2: WhatsApp NSFW Inline Image Attempts

**What goes wrong:** Sending NSFW images directly through WhatsApp messages (inline attachments or media URLs). WhatsApp detects policy violations through automated scanning, leading to:
- Immediate message blocking
- Account throttling (rate limits on messages)
- Permanent account suspension

**Why it happens:** Developers assume WhatsApp Business API allows all content types if user consents. Policy explicitly prohibits "offensive content... sexually explicit materials or nudity, determined at WhatsApp's sole discretion."

**How to avoid:**
- **Never send NSFW images via WhatsApp messages** (inline or as attachments)
- Use web portal architecture (Pattern 4): generate image, upload to private storage, send HTTPS link via WhatsApp
- Text-only intimate conversations on WhatsApp; images delivered via authenticated web links
- Test with mild content first; monitor account health dashboard

**Warning signs:**
- Planning to send `image/jpeg` attachments in intimate mode
- Assuming end-to-end encryption prevents WhatsApp from detecting NSFW content (it doesn't)
- Not reading WhatsApp Business Commerce Policy prohibited content list

### Pitfall 3: Insufficient Audit Logging Granularity

**What goes wrong:** Logging only "user logged in" or "image generated" without context. When regulator asks "Show me all images generated for user X on date Y" or "Prove you blocked non-consensual content requests," you can't comply.

**Why it happens:** Minimal logging feels sufficient during development. Compliance requirements aren't considered until audit time.

**How to avoid:**
- Log all compliance-relevant events: age verification, content blocks, image generation, account deletion, takedown requests
- Include context in `event_data` JSONB: spice level, content categories, policy triggers, user actions
- Quarterly compliance drill: "Can we answer: Who generated what, when, and why was it allowed/blocked?"
- Retention policy: 2 years minimum (GDPR), jurisdiction-specific requirements may differ

**Warning signs:**
- Generic log messages without user_id or timestamps
- No logging of moderation events (content blocks, refusals)
- Logs stored in application logs (not queryable database)

### Pitfall 4: TAKE IT DOWN Act Misinterpretation

**What goes wrong:** Assuming TAKE IT DOWN Act applies to AI-generated images of fictional characters. Implementing 48-hour takedown process for fictional content wastes engineering time.

**Why it happens:** Act covers "digital forgeries" (AI-generated), leading to confusion. However, it specifically targets "intimate visual depictions of an identifiable individual"—real people whose likeness is forged or used without consent.

**How to avoid:**
- **Clarify scope:** TAKE IT DOWN Act applies to AI-generated deepfakes of real, identifiable people (e.g., celebrity face swapped onto pornography)
- **Platform context:** Ava generates fictional characters from user descriptions, not deepfakes of real people
- **Still document process:** Even if not legally required, having a takedown process is best practice for edge cases (user uploads real person's photo as avatar reference)
- **48-hour timeline:** If implementing takedown, commit to "acknowledged within 24 hours, content removed within 48 hours"

**Warning signs:**
- Building takedown infrastructure before clarifying if platform hosts user-uploaded images of real people
- Confusing "AI-generated" (broad) with "digital forgery of identifiable individual" (narrow legal term)

### Pitfall 5: Account Deletion Without Full Data Erasure

**What goes wrong:** Implementing "delete account" that removes database row but leaves:
- Generated images in S3/CDN
- Cached data in Redis/memory
- Audit logs with PII
- Backup databases not updated

Result: GDPR violations, regulatory fines, loss of user trust.

**Why it happens:** Developers focus on primary database deletion, forget distributed data storage.

**How to avoid:**
- **Inventory all user data locations:** Database, object storage, CDN, caches, backups, audit logs
- **Cascading deletion:** Trigger deletion across all systems: `DELETE FROM users WHERE id = X` → trigger S3 deletion → purge CDN cache → anonymize audit logs
- **Anonymization vs deletion:** Audit logs can retain events but replace user_id with anonymized token: `user_id = 'deleted_user_abc123'`
- **Test deletion:** Create test account, generate content, delete, verify all traces removed
- **Audit trail of deletion:** Log deletion event itself (proves compliance if questioned)

**Warning signs:**
- Single `DELETE FROM users` query without cascading logic
- No deletion testing in staging environment
- Generated images remain accessible after account deletion

### Pitfall 6: Overly Aggressive Content Filtering

**What goes wrong:** Content moderation AI flags legitimate intimate content as policy violations. Users get constant refusals in intimate mode, destroying user experience.

**Why it happens:** Moderation APIs (OpenAI, Azure) are calibrated for general-purpose platforms, not adult content. Default settings block all sexual content, not just policy violations.

**How to avoid:**
- **Calibrate thresholds:** Sexual content is allowed (platform's purpose); only forbidden categories trigger refusals
- **Custom classifier for non-consent:** OpenAI Moderation doesn't detect "non-consensual scenarios" specifically—requires semantic analysis or fine-tuned classifier
- **Tiered moderation:** Light filtering in intimate mode (catch only forbidden categories), strict filtering in secretary mode (no sexual content)
- **User feedback loop:** Log false positives (blocked content that shouldn't be), retrain classifiers

**Warning signs:**
- Using moderation API's default "sexual" category to block all intimate content
- No distinction between "sexual content" (allowed) and "non-consensual sexual content" (forbidden)
- High refusal rate in intimate mode (>10% of messages blocked)

### Pitfall 7: Storing Age Verification PII Unnecessarily

**What goes wrong:** Logging IP addresses, timestamps, device fingerprints, or selfie images from age verification. Creates GDPR liability and increases attack surface.

**Why it happens:** "More data is better for compliance" intuition. Actually, GDPR requires data minimization.

**How to avoid:**
- **Self-declaration:** Log only `user_id`, `verified: true`, `method: 'self-declaration'`—no timestamp, no IP, no device data
- **Future ID verification:** Third-party services (Onfido, Veriff) handle PII; receive only verification result token
- **Audit logs:** Record verification event, not verification data
- **Data retention:** Delete verification artifacts immediately after result obtained

**Warning signs:**
- Storing uploaded ID documents or selfies after verification
- Logging IP addresses "just in case"
- Retaining verification session data indefinitely

## Code Examples

Verified patterns from research and industry best practices:

### Age Verification Checkbox (Self-Declaration)

**Signup flow with age declaration:**

```html
<!-- Age verification UI -->
<form id="signup-form">
  <h2>Create Your Account</h2>

  <label for="email">Email</label>
  <input type="email" id="email" required>

  <label for="password">Password</label>
  <input type="password" id="password" required>

  <!-- Age verification (required, blocks access if declined) -->
  <div class="age-verification-section">
    <h3>Age Verification</h3>
    <p>This platform contains adult content. You must be 18 or older to use this service.</p>

    <label>
      <input type="checkbox" id="age-declaration" required>
      I confirm that I am 18 years of age or older
    </label>

    <p class="legal-notice">
      By checking this box, you certify that you are of legal age to access adult content
      in your jurisdiction. False declaration may result in account termination and legal consequences.
    </p>
  </div>

  <button type="submit">Create Account</button>
</form>

<script>
// Frontend validation
document.getElementById('signup-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const ageVerified = document.getElementById('age-declaration').checked;

  if (!ageVerified) {
    alert('You must confirm you are 18+ to create an account.');
    return;
  }

  // Submit to backend
  const response = await fetch('/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: document.getElementById('email').value,
      password: document.getElementById('password').value,
      ageVerified18Plus: ageVerified
    })
  });

  if (response.ok) {
    window.location.href = '/dashboard';
  }
});
</script>
```

**Backend verification:**

```typescript
// Backend: /api/auth/signup
async function handleSignup(req: Request, res: Response) {
  const { email, password, ageVerified18Plus } = req.body;

  // Reject if age verification declined
  if (!ageVerified18Plus) {
    return res.status(403).json({
      error: 'Age verification required',
      message: 'You must be 18+ to create an account'
    });
  }

  // Create user account
  const userId = await createUser(email, password);

  // Log age verification (audit trail)
  await auditLog.record({
    event: 'age_verification',
    userId,
    event_category: 'auth',
    action: 'verify',
    result: 'success',
    event_data: {
      method: 'self-declaration',
      version: 1
    }
  });

  return res.status(201).json({ userId, message: 'Account created' });
}
```

**Note:** This implementation does NOT store timestamp, IP address, or device fingerprint (data minimization).

### Audit Log Helper Functions

**Logging wrapper for consistent audit entries:**

```typescript
// audit-logger.ts
import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

interface AuditLogEntry {
  userId: string;
  eventType: string;
  eventCategory: 'auth' | 'content' | 'moderation' | 'account';
  action: 'create' | 'read' | 'update' | 'delete' | 'verify' | 'block';
  resourceType?: string;
  resourceId?: string;
  eventData?: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
  sessionId?: string;
  result: 'success' | 'failure' | 'blocked';
  errorMessage?: string;
}

export async function logAuditEvent(entry: AuditLogEntry): Promise<void> {
  const query = `
    INSERT INTO audit_log (
      id, user_id, event_type, event_category, action,
      resource_type, resource_id, event_data,
      ip_address, user_agent, session_id, result, error_message
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
  `;

  const values = [
    uuidv4(),
    entry.userId,
    entry.eventType,
    entry.eventCategory,
    entry.action,
    entry.resourceType || null,
    entry.resourceId || null,
    JSON.stringify(entry.eventData || {}),
    entry.ipAddress || null,
    entry.userAgent || null,
    entry.sessionId || null,
    entry.result,
    entry.errorMessage || null
  ];

  await pool.query(query, values);
}

// Convenience functions
export const auditLog = {
  ageVerification: (userId: string, method: string, verified: boolean) =>
    logAuditEvent({
      userId,
      eventType: 'age_verification',
      eventCategory: 'auth',
      action: 'verify',
      result: verified ? 'success' : 'failure',
      eventData: { method, version: 1 }
    }),

  contentBlock: (userId: string, category: string, resourceId?: string) =>
    logAuditEvent({
      userId,
      eventType: 'content_block',
      eventCategory: 'moderation',
      action: 'block',
      resourceType: 'conversation',
      resourceId,
      result: 'blocked',
      eventData: { trigger: 'forbidden_category', category }
    }),

  imageGeneration: (userId: string, imageId: string, spiceLevel: string, model: string) =>
    logAuditEvent({
      userId,
      eventType: 'image_generation',
      eventCategory: 'content',
      action: 'create',
      resourceType: 'image',
      resourceId: imageId,
      result: 'success',
      eventData: { model, spiceLevel }
    }),

  accountDeletion: (userId: string, stats: { conversations: number; images: number }) =>
    logAuditEvent({
      userId,
      eventType: 'account_deletion',
      eventCategory: 'account',
      action: 'delete',
      resourceType: 'account',
      result: 'success',
      eventData: {
        deleted_conversations: stats.conversations,
        deleted_images: stats.images,
        deletion_requested_at: new Date().toISOString()
      }
    })
};
```

**Usage in application:**

```typescript
// Example: Log content moderation block
async function handleUserMessage(userId: string, message: string) {
  const safetyCheck = await contentSafety.analyze(message);

  if (safetyCheck.violatesPolicy) {
    await auditLog.contentBlock(userId, safetyCheck.category);
    return getRefusalMessage(safetyCheck.category);
  }

  // Continue with message handling...
}

// Example: Log image generation
async function generateImage(userId: string, prompt: string, spiceLevel: string) {
  const imageId = uuidv4();
  const imageUrl = await imageAPI.generate(prompt);

  await auditLog.imageGeneration(userId, imageId, spiceLevel, 'stable-diffusion-xl');

  return { imageId, imageUrl };
}
```

### Cascading Account Deletion (GDPR Right to Erasure)

**Complete data deletion across all systems:**

```typescript
// account-deletion.ts
import { S3Client, ListObjectsV2Command, DeleteObjectsCommand } from '@aws-sdk/client-s3';
import { auditLog } from './audit-logger';

const s3Client = new S3Client({ region: process.env.AWS_REGION });

interface DeletionStats {
  conversations: number;
  images: number;
  auditLogsAnonymized: number;
}

export async function deleteUserAccount(userId: string): Promise<DeletionStats> {
  const stats: DeletionStats = { conversations: 0, images: 0, auditLogsAnonymized: 0 };

  // Step 1: Delete conversations from database
  const conversationResult = await pool.query(
    'DELETE FROM conversations WHERE user_id = $1 RETURNING id',
    [userId]
  );
  stats.conversations = conversationResult.rowCount || 0;

  // Step 2: Delete generated images from S3
  const imageListResponse = await s3Client.send(new ListObjectsV2Command({
    Bucket: process.env.S3_BUCKET,
    Prefix: `users/${userId}/images/`
  }));

  if (imageListResponse.Contents && imageListResponse.Contents.length > 0) {
    const objectsToDelete = imageListResponse.Contents.map(obj => ({ Key: obj.Key! }));

    await s3Client.send(new DeleteObjectsCommand({
      Bucket: process.env.S3_BUCKET,
      Delete: { Objects: objectsToDelete }
    }));

    stats.images = objectsToDelete.length;
  }

  // Step 3: Purge CDN cache (if using Cloudflare/CloudFront)
  await purgeCDNCache(`/users/${userId}/*`);

  // Step 4: Anonymize audit logs (retain events, remove PII)
  const anonymizedId = `deleted_user_${uuidv4().substring(0, 8)}`;
  const auditResult = await pool.query(
    'UPDATE audit_log SET user_id = $1 WHERE user_id = $2 RETURNING id',
    [anonymizedId, userId]
  );
  stats.auditLogsAnonymized = auditResult.rowCount || 0;

  // Step 5: Delete user account record
  await pool.query('DELETE FROM users WHERE id = $1', [userId]);

  // Step 6: Log deletion event (with anonymized ID for audit trail)
  await auditLog.accountDeletion(anonymizedId, {
    conversations: stats.conversations,
    images: stats.images
  });

  return stats;
}

// Purge CDN cache (Cloudflare example)
async function purgeCDNCache(pattern: string): Promise<void> {
  // Implementation depends on CDN provider
  // Cloudflare: await cloudflare.zones.purgeCache({ files: [pattern] })
  // CloudFront: await cloudfront.createInvalidation({ Paths: [pattern] })
}
```

**User-facing deletion endpoint:**

```typescript
// DELETE /api/account
async function handleAccountDeletion(req: Request, res: Response) {
  const userId = req.user.id; // From authentication middleware

  // Confirm deletion intent
  const { confirmDeletion } = req.body;
  if (confirmDeletion !== 'DELETE_MY_ACCOUNT') {
    return res.status(400).json({
      error: 'Confirmation required',
      message: 'Send { "confirmDeletion": "DELETE_MY_ACCOUNT" } to confirm'
    });
  }

  // Execute deletion
  const stats = await deleteUserAccount(userId);

  // Return confirmation
  return res.status(200).json({
    message: 'Account permanently deleted',
    deleted: {
      conversations: stats.conversations,
      images: stats.images,
      auditLogsAnonymized: stats.auditLogsAnonymized
    },
    note: 'This action is irreversible. All data has been permanently removed.'
  });
}
```

### 48-Hour Takedown Process Documentation

**Process flowchart (Markdown documentation):**

```markdown
# Content Takedown Process

## Scope
This process applies to requests for removal of AI-generated images that allegedly:
- Depict an identifiable real person without consent (deepfake)
- Violate intellectual property rights
- Contain illegal content

**Note:** TAKE IT DOWN Act applies to deepfakes of real people, not fictional characters.
Ava generates fictional characters—this process is for edge cases (e.g., user uploads real person photo as avatar reference).

## Timeline
- **Acknowledgment:** Within 24 hours of receiving valid takedown request
- **Review & Action:** Within 48 hours of acknowledgment (72 hours total from request)

## Request Requirements
Takedown requests must include:
1. **Requestor identity:** Name, email, phone number
2. **Proof of identity:** For depicted individual, government-issued ID or other verification
3. **Content identification:** URL or image ID of content to be removed
4. **Statement of non-consent:** "I did not consent to the creation or distribution of this image"
5. **Good faith statement:** "I have a good faith belief this content violates [policy/law]"
6. **Signature:** Physical or electronic signature

Submit requests to: takedown@ava-platform.com

## Review Process

### Step 1: Acknowledgment (Within 24 hours)
- Log request in `takedown_requests` database table
- Send acknowledgment email: "We received your request (ID: XXX) and will review within 48 hours"
- Assign case ID and reviewing staff member

### Step 2: Validation (Within 48 hours)
- Verify requestor identity
- Confirm content exists in our system
- Determine if request is valid:
  - **Valid:** Content depicts identifiable real person OR violates clear policy
  - **Invalid:** Content is fictional character generated from user's description (no real person depicted)

### Step 3: Action (Within 48 hours)
**If valid:**
1. Remove image from storage (S3/CDN)
2. Purge all cached versions
3. Revoke signed URLs
4. Log removal in audit_log: `event_type: 'takedown_removal'`
5. Notify requestor: "Content removed (ID: XXX)"

**If invalid:**
1. Send detailed explanation: "Content does not depict identifiable individual; TAKE IT DOWN Act does not apply to fictional characters"
2. Offer alternative: "If content violates other policies, please specify which policy"

### Step 4: Counter-Notice (Optional)
If content creator (user) believes removal was erroneous:
1. Submit counter-notice with explanation
2. Review within 10 business days
3. If counter-notice valid, restore content and notify both parties

## Database Schema

```sql
CREATE TABLE takedown_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    requestor_email VARCHAR(255) NOT NULL,
    requestor_name VARCHAR(255),
    content_url TEXT NOT NULL,
    content_id UUID,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'received', 'reviewing', 'completed', 'rejected'
    action_taken VARCHAR(50), -- 'content_removed', 'rejected_not_applicable', 'counter_notice_upheld'
    reviewer_id UUID,
    reviewed_at TIMESTAMPTZ,
    notes TEXT
);
```

## Audit Trail
All takedown actions logged in `audit_log`:
- `event_type: 'takedown_request_received'`
- `event_type: 'takedown_review_completed'`
- `event_type: 'takedown_content_removed'`
```

## State of the Art

| Old Approach (2023-2024) | Current Approach (2026) | When Changed | Impact |
|--------------------------|-------------------------|--------------|--------|
| Simple age gates (birthdate input) | "Commercially reasonable" age verification (ID check, biometric, or third-party service) | January 2026 (Texas, Utah, Louisiana app store laws) | Self-declaration alone no longer sufficient in many states; platforms must implement stronger verification or face penalties |
| Generic ToS templates | Specialized attorney review for adult platforms | Ongoing (increased enforcement) | Liability for AI-generated content requires explicit disclaimers, user responsibility clauses, and jurisdiction-specific compliance |
| Metadata-only content credentials | C2PA 2.1 with digital watermarks | April 2025 (C2PA 2.1 release) | Watermarks survive social media uploads and resist tampering; metadata alone was easily stripped |
| Manual moderation queues | Real-time AI content safety APIs | 2024-2025 (API maturity) | OpenAI Moderation, Azure Content Safety, Anthropic safety classifiers enable instant blocking; manual review remains for edge cases |
| "Right to be forgotten" as optional feature | Mandatory GDPR right to erasure enforcement | 2026 (EDPB coordinated enforcement) | Platforms must demonstrate complete data deletion within 1 month; incomplete erasure results in fines |
| Inline NSFW images on messaging platforms | Web portal delivery with authenticated links | Ongoing (platform policy enforcement) | WhatsApp, Telegram, Discord increasingly ban NSFW content in messages; web portal architecture preserves access while complying with platform policies |

**Deprecated/outdated:**
- **Age gates with no verification:** Simple "Enter your birthdate" screens without validation are no longer compliant in states with age verification laws
- **DMCA-only takedown processes:** TAKE IT DOWN Act (2025) requires specific 48-hour process for non-consensual intimate imagery, separate from copyright claims
- **Storing uploaded ID documents:** Privacy-preserving verification (third-party APIs, zero-knowledge proofs) replaces storing copies of government IDs

## Open Questions

### 1. California AB 316 Liability for AI Outputs

**What we know:** California's AB 316 (effective 2026) bans the "autonomous-harm defense"—users can't claim "the AI did it" to escape liability for misleading ads, fake medical advice, or consumer protection violations.

**What's unclear:** Does this extend to NSFW content generation? If user requests non-consensual scenario and bot refuses, but user jailbreaks the prompt and generates content—is user or platform liable?

**Recommendation:** ToS must explicitly state: "You are solely responsible for content you generate using this platform, including any attempts to circumvent content guardrails. Platform liability is limited to [specific limits]." Attorney review required for final language.

### 2. State-Specific Age Verification Timeline

**What we know:** Texas (Jan 1, 2026), Utah (May 7, 2026), Louisiana (July 1, 2026), California (Jan 1, 2027) require "commercially reasonable" age verification for apps distributing adult content.

**What's unclear:** Is self-declaration "commercially reasonable"? Texas law doesn't define the threshold. Will enforcement prioritize platforms without any verification, or will self-declaration also be challenged?

**Recommendation:** Launch with self-declaration + pluggable architecture. Monitor enforcement actions in Q2-Q3 2026. If self-declaration challenged, upgrade to third-party verification (Onfido, Stripe Identity) as needed.

### 3. WhatsApp Business API Long-Term Viability

**What we know:** WhatsApp prohibits sexually explicit materials in messages. Web portal workaround (text-only on WhatsApp, images via links) is compliant today.

**What's unclear:** Will WhatsApp tighten enforcement to ban platforms whose *purpose* is NSFW content, even if images aren't sent inline? Precedent: OnlyFans links were briefly banned on Instagram (2021), then policy reversed.

**Recommendation:**
- Build WhatsApp integration but don't make it sole platform (web app in Phase 6 is critical fallback)
- Monitor WhatsApp Business API policy updates quarterly
- Prepare migration plan: if WhatsApp bans platform, pivot to web app + push notifications

### 4. Multi-Jurisdiction Compliance at Scale

**What we know:** GDPR (EU), CCPA (California), and other privacy laws have conflicting requirements (e.g., GDPR's right to erasure vs. some jurisdictions' data retention mandates).

**What's unclear:** When scaling internationally, which jurisdiction's laws apply? User's location, server location, company incorporation, or all three?

**Recommendation:**
- Phase 1: Document general best-practice compliance (no specific jurisdiction)
- Before international expansion: Engage attorney to assess jurisdiction-specific requirements
- Consider geo-blocking (e.g., unavailable in EU until GDPR compliance fully implemented)

## Validation Architecture

**Note:** Validation architecture section is NOT APPLICABLE for Phase 1. The `workflow.nyquist_validation` flag in `.planning/config.json` is not set to `true`, and Phase 1 focuses on documentation and schema design rather than production code requiring continuous test validation.

Phase 1 deliverables are:
- Terms of Service documents (Markdown)
- Content policy documentation (Markdown)
- Database schema SQL files
- Architecture decision records (Markdown)

**Validation approach for Phase 1:** Manual review of documents by attorney (external validation), schema tested via SQL execution against local PostgreSQL instance (not automated CI test suite).

**Nyquist validation will apply to later phases** when production code is implemented (Phases 2-7).

## Sources

### Primary (HIGH confidence)
- [The New Age-Verification Reality: Compliance in a Rapidly Expanding State Regulatory Landscape](https://natlawreview.com/article/new-age-verification-reality-compliance-rapidly-expanding-state-regulatory) - 2026 state age verification law overview
- [TAKE IT DOWN Act: The next bipartisan US federal privacy, AI law](https://iapp.org/news/a/take-it-down-act-the-next-bipartisan-us-federal-privacy-ai-law) - Federal non-consensual intimate imagery law requirements
- [Let's Build Production-Ready Audit Logs in PostgreSQL](https://medium.com/@sehban.alam/lets-build-production-ready-audit-logs-in-postgresql-7125481713d8) - PostgreSQL audit schema design patterns
- [WhatsApp Business Policy](https://business.whatsapp.com/policy) - Official prohibited content policy
- [C2PA 2.1 - Strengthening Content Credentials with Digital Watermarks](https://www.digimarc.com/blog/c2pa-21-strengthening-content-credentials-digital-watermarks) - Content provenance standard

### Secondary (MEDIUM confidence)
- [AI Influencer Legal Guide 2026 | Compliance & Protection](https://apatero.ai/blog/ai-influencer-legal-guide-2026) - AI content platform legal considerations
- [Let Them Down Easy! Contextual Effects of LLM Guardrails on User Perceptions and Preferences](https://arxiv.org/html/2506.00195) - Research on refusal message UX
- [Complete GDPR Compliance Guide (2026-Ready)](https://secureprivacy.ai/blog/gdpr-compliance-2026) - Right to erasure implementation
- [The 2026 Outlook on US Age Verification Laws | Ondato Report](https://ondato.com/reports/the-us-age-verification-laws-2026-outlook/) - Age verification methods and enforcement trends
- [Database Design for Audit Logging | Redgate](https://www.red-gate.com/blog/database-design-for-audit-logging) - Audit schema best practices

### Tertiary (LOW confidence - marked for validation)
- [How fast is too slow when it comes to DMCA content removal?](https://www.zwillgen.com/general/speed-matters-jury-decide-whether-48-hour-response-time-copyright-takedown-notice-sufficiently-expeditious/) - Legal precedent for "expeditious" takedown timelines (DMCA-specific, not TAKE IT DOWN Act)
- Online legal forums discussing adult platform ToS requirements - Anecdotal advice, not official guidance

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - PostgreSQL audit logging well-documented; attorney review requirement clear but no standardized process
- Architecture: HIGH - Pluggable verification pattern well-established; WhatsApp NSFW restrictions verified in official policy
- Pitfalls: HIGH - Self-declaration insufficiency documented in 2026 state laws; WhatsApp inline image ban verified; audit logging gaps are common compliance failure
- TAKE IT DOWN Act applicability: HIGH - Act explicitly targets "identifiable individuals" (real people), not fictional characters
- C2PA watermarking: MEDIUM - Standard exists (C2PA 2.1), but implementation complexity high; defer to Phase 7 as planned

**Research date:** 2026-02-23
**Valid until:** ~60 days (March 2026) — regulatory landscape evolving rapidly; quarterly re-check recommended

**Critical uncertainties:**
- State enforcement of self-declaration age verification (will it be challenged?)
- WhatsApp's long-term tolerance of NSFW platforms using text-only + web portal architecture
- California AB 316 liability boundaries for AI-generated content

**Next steps for planner:**
1. Create Wave 0 plan: Set up PostgreSQL, install audit schema, create test audit log entries
2. Create documentation plans: ToS structure, content policy, takedown process, ADRs
3. Defer production code enforcement (guardrails, takedown API endpoints) to Phase 2+
