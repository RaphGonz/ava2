---
phase: 14
slug: apply-the-style-of-the-front-page-to-the-rest-of-the-ui-of-the-entire-app
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest ^4.0.18 + @testing-library/react ^16.3.2 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm test -- --run` |
| **Full suite command** | `cd frontend && npm test -- --run` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test -- --run`
- **After every plan wave:** Run `cd frontend && npm test -- --run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | UI-nav | unit | `cd frontend && npm test -- --run AppNav` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | UI-nav | smoke | `cd frontend && npm test -- --run` | ✅ | ⬜ pending |
| 14-02-01 | 02 | 2 | UI-auth | smoke | `cd frontend && npm test -- --run LoginPage` | ❌ W0 | ⬜ pending |
| 14-02-02 | 02 | 2 | UI-auth | smoke | `cd frontend && npm test -- --run` | ✅ | ⬜ pending |
| 14-03-01 | 03 | 2 | UI-chat | unit | `cd frontend && npm test -- --run ChatBubble` | ❌ W0 | ⬜ pending |
| 14-03-02 | 03 | 2 | UI-chat | smoke | `cd frontend && npm test -- --run` | ✅ | ⬜ pending |
| 14-04-01 | 04 | 2 | UI-settings | smoke | `cd frontend && npm test -- --run` | ✅ | ⬜ pending |
| 14-04-02 | 04 | 2 | UI-landing | smoke | `cd frontend && npm test -- --run LandingPage` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/components/AppNav.test.tsx` — renders chat/photos/settings links + active state
- [ ] `frontend/src/pages/LoginPage.test.tsx` — dark theme render (bg-black presence, GlassCard)
- [ ] `frontend/src/components/ChatBubble.test.tsx` — gradient user bubble, glass Ava bubble classes

*Existing: `LandingPage.test.tsx`, `AdminPage.test.tsx` — must stay GREEN throughout.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| All pages have black background | UI-theme | Visual-only, no DOM class assertion | Open each page, confirm bg-black |
| Gradient buttons match landing page | UI-theme | Visual fidelity | Compare auth CTA, nav buttons with landing |
| Bottom tab bar works on mobile | UI-nav | Responsive layout | Resize browser to 375px, confirm tab bar visible |
| Hero right mockup shows chat + locked photo | UI-landing | Visual content | Open landing page, verify right mockup |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
