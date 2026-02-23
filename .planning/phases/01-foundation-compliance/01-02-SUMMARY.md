---
phase: 01-foundation-compliance
plan: 02
subsystem: compliance
tags: [compliance, legal, age-verification, content-policy, whatsapp, audit-log, SAFE-01, SAFE-02, PLAT-03]

dependency_graph:
  requires:
    - phase: 01-foundation-compliance-plan-01
      provides: audit_log database schema, takedown_requests schema
  provides:
    - terms-of-service framework covering AI content liability and account deletion
    - content policy with 6 forbidden categories and system-level refusal design
    - age verification strategy with pluggable AgeVerificationProvider architecture
    - ADR-001 pluggable age verification TypeScript interface
    - ADR-002 WhatsApp text-only + web portal JWT image delivery architecture
    - ADR-003 consolidated audit_log design rationale and data minimization approach
  affects:
    - Phase 2 (User Management): age verification flow, account deletion implementation
    - Phase 3 (Mode Switching): secretary mode boundary enforcement
    - Phase 5 (Intimate Mode): content policy enforcement, spice level control
    - Phase 6 (Web Portal): JWT-signed image URL delivery implementation
    - Phase 7 (Image Generation): content moderation, audit logging for image events

tech_stack:
  added: []
  patterns:
    - Provider pattern for pluggable age verification (AgeVerificationProvider interface)
    - JWT-signed short-lived URLs for NSFW image delivery via web portal
    - System-level refusal messages (red box design, breaks persona) for content policy violations
    - Data minimization: no PII beyond user_id in audit trail

key_files:
  created:
    - compliance/policies/terms-of-service.md
    - compliance/policies/content-policy.md
    - compliance/policies/age-verification-strategy.md
    - compliance/architecture-decisions/adr-001-age-verification.md
    - compliance/architecture-decisions/adr-002-whatsapp-nsfw.md
    - compliance/architecture-decisions/adr-003-audit-logging.md
  modified: []

key-decisions:
  - "Self-declaration checkbox (18+) as Phase 1 age verification, all checks go through AgeVerificationManager.verifyAge() never direct flag checks"
  - "WhatsApp text-only intimate mode: NSFW images delivered via JWT-signed web portal links (24h expiry), not as WhatsApp attachments"
  - "Avatar age floor of 20+ (not 18+) enforced separately from account age — hard DB constraint and form validation"
  - "Content policy refusals are system-level red-box messages that break persona — flat refusal, no lockout, no escalation"
  - "Spice control: floor + ceiling setting (low/medium/high/max), 'stop' safe word lowers one notch rather than resetting to zero"
  - "Data minimization: no timestamp, IP, or device fingerprint stored for age verification events"

patterns-established:
  - "Provider pattern: all verification logic through abstraction layer, swap via config not code"
  - "Append-only audit trail: database trigger protects against UPDATE/DELETE"
  - "Secretary mode deflection: playful ('shh, not now') not cold rejection"

requirements-completed: [SAFE-01, SAFE-02, PLAT-03]

duration: 15min
completed: 2026-02-23
---

# Phase 01 Plan 02: Policy Documents and ADRs Summary

**ToS, content policy, age verification strategy, and 3 ADRs establishing full legal/architectural compliance framework for Ava's NSFW features**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-23T10:21:20Z
- **Completed:** 2026-02-23T10:36:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created 3 policy documents (ToS, content policy, age verification strategy) covering legal framework, 6 forbidden categories, pluggable verification, and 20+ avatar floor
- Created 3 ADRs documenting the pluggable age verification provider pattern (TypeScript interface), WhatsApp web portal image delivery architecture, and consolidated audit log design
- All documents include attorney review notices, DRAFT status, and cross-references to related documents

## Task Commits

Each task was committed atomically:

1. **Task 1: Create policy documents (ToS, content policy, age verification strategy)** - `0ca14d4` (feat)
2. **Task 2: Create Architecture Decision Records** - `1571229` (feat)

## Files Created/Modified

- `compliance/policies/terms-of-service.md` - Legal framework: service description, 18+ eligibility, jailbreak liability clause, AI-generated content disclaimer, account deletion, governing law placeholder
- `compliance/policies/content-policy.md` - 6 forbidden categories with red-box refusal design, spice level control (low/medium/high/max), secretary mode boundary, future moderation API approach
- `compliance/policies/age-verification-strategy.md` - Self-declaration Phase 1 approach, data minimization, AgeVerificationProvider interface, 20+ avatar floor enforcement, regulatory upgrade path
- `compliance/architecture-decisions/adr-001-age-verification.md` - Full TypeScript interface for AgeVerificationProvider, SelfDeclarationProvider implementation, IDVerificationProvider stub, configuration-driven provider selection
- `compliance/architecture-decisions/adr-002-whatsapp-nsfw.md` - ASCII architecture diagram for WhatsApp text-only + S3 + JWT + web portal flow, security considerations, alternatives rejected
- `compliance/architecture-decisions/adr-003-audit-logging.md` - Consolidated audit_log table design rationale, JSONB flexibility, append-only enforcement, data minimization policy, retention approach

## Decisions Made

- **Provider pattern for age verification:** All application code calls `AgeVerificationManager.verifyAge()`, never checks `user.ageVerified` flags directly. Swapping from self-declaration to ID verification is a config change, not a code rewrite. Regulatory risk justifies slight over-engineering for Phase 1.
- **WhatsApp NSFW image delivery via web portal:** WhatsApp explicitly prohibits sexually explicit materials. Text-only messages with JWT-signed links to a secure web portal solves compliance while providing a better viewing experience (full-screen vs. thumbnail). Accepted UX tradeoff: one extra click.
- **Avatar age floor 20+ (not 18+):** Provides safety margin above legal minimum, eliminates ambiguity about character maturity. Enforced at DB level (CHECK constraint) and form validation — cannot be bypassed.
- **Content refusals are system-level, not in-character:** Red box breaks persona deliberately to make platform boundary clear vs. character behavior. Flat refusal every time — no strikes, no lockout.
- **Data minimization for age verification:** No timestamp, IP address, or device fingerprint stored for age verification events. Only user_id + verified:true + method:'self-declaration' logged in audit_log.

## Deviations from Plan

None — plan executed exactly as written.

All tasks completed without auto-fixes, architectural changes, or blockers.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. All files are documentation only.

## Next Phase Readiness

- Compliance framework complete: ToS, content policy, age verification strategy, and 3 ADRs all ready for attorney review
- Phase 2 (User Management & WhatsApp) can use this framework as implementation guide:
  - Age verification flow: implement SelfDeclarationProvider per ADR-001
  - Account deletion: anonymize audit logs per ToS section 6
  - Secretary mode boundaries: deflect with "shh, not now" per content policy section 2.2
- Phase 6 (Web Portal): must implement JWT-signed image URL endpoint per ADR-002 architecture
- No blockers for subsequent phases

---

## Self-Check: PASSED

**Files:**
- [x] FOUND: compliance/policies/terms-of-service.md
- [x] FOUND: compliance/policies/content-policy.md
- [x] FOUND: compliance/policies/age-verification-strategy.md
- [x] FOUND: compliance/architecture-decisions/adr-001-age-verification.md
- [x] FOUND: compliance/architecture-decisions/adr-002-whatsapp-nsfw.md
- [x] FOUND: compliance/architecture-decisions/adr-003-audit-logging.md

**Commits:**
- [x] FOUND: 0ca14d4 (Task 1 - policy documents)
- [x] FOUND: 1571229 (Task 2 - ADRs)

All artifacts exist and are committed. Plan execution complete.

---

*Phase: 01-foundation-compliance*
*Completed: 2026-02-23*
*Execution time: ~15 minutes*
*Next plan: Phase 2 (User Management & WhatsApp)*
