# Requirements: Ava — v1.2 Cookie Banner

**Defined:** 2026-03-16
**Core Value:** A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app or web app the user already uses.

## v1 Requirements

### Cookie Consent

- [ ] **COOK-01**: Visitor sees a cookie consent banner on the landing page before any non-essential scripts load
- [ ] **COOK-02**: Visitor can accept all cookies (Sentry + analytics enabled)
- [ ] **COOK-03**: Visitor can decline non-essential cookies (Sentry + analytics blocked; Stripe still loads)
- [x] **COOK-04**: Consent choice is saved to localStorage and persists across sessions
- [ ] **COOK-05**: Banner does not appear again once a choice has been made
- [x] **COOK-06**: Sentry and analytics scripts only initialise after consent is granted (not on page load)

## v2 Requirements

*(None identified for this milestone)*

## Out of Scope

| Feature | Reason |
|---------|--------|
| Consent editable in Settings UI | localStorage-only for v1.2; revisit if legally required |
| Authenticated pages banner | Logged-in users accepted via ToS; landing page only |
| Granular per-category consent | Accept/decline all is sufficient for current cookie types |
| Server-side consent storage | No cross-device sync needed; localStorage sufficient |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| COOK-01 | Phase 17 | Pending |
| COOK-02 | Phase 17 | Pending |
| COOK-03 | Phase 17 | Pending |
| COOK-04 | Phase 17 | Complete |
| COOK-05 | Phase 17 | Pending |
| COOK-06 | Phase 17 | Complete |

**Coverage:**
- v1 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-16*
*Last updated: 2026-03-16 — traceability confirmed after roadmap creation*
