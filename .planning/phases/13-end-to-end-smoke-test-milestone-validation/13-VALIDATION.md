---
phase: 13
slug: end-to-end-smoke-test-milestone-validation
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-10
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-asyncio 0.21.x |
| **Config file** | none — runs from `backend/` directory |
| **Quick run command** | `cd backend && python -m pytest tests/test_smoke_paywall.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds (automated portion) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_smoke_paywall.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | ADMN-02, ADMN-03, SC-5 | smoke | `cd backend && python -m pytest tests/test_smoke_paywall.py tests/test_smoke_usage_events.py -x -q` | ❌ W0 | ⬜ pending |
| 13-01-02 | 01 | 1 | All v1.1 | doc | n/a — runbook document | n/a | ⬜ pending |
| 13-02-01 | 02 | 2 | ADMN-02, ADMN-03, SC-5 | smoke | `cd backend && python -m pytest tests/test_smoke_paywall.py tests/test_smoke_usage_events.py -x -q` | ✅ after 13-01 | ⬜ pending |
| 13-02-02 | 02 | 2 | All v1.1 | manual | Human runbook execution | n/a | ⬜ pending |
| 13-02-03 | 02 | 2 | All v1.1 | doc | `grep -E "SHIPPED|BLOCKED" docs/smoke-test-runbook.md` | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_smoke_paywall.py` — SC-5 (paywall 402), ADMN-03 (403 non-admin)
- [ ] `backend/tests/test_smoke_usage_events.py` — ADMN-02 (usage_events event types)
- [ ] `backend/tests/conftest.py` — `unsubscribed_jwt` and `regular_user_jwt` fixtures

*All other criteria are manual-only (browser + async pipelines require human observation).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Reference image appears within 5 min | INFRA-01/02/03/04, SC-1 | Async ComfyUI pipeline, requires real avatar upload | Sign up, upload selfie, wait 5 min, confirm non-null reference_image_url |
| Secretary chat reply | SC-2 | Requires production OpenAI key + live session | Send message, confirm reply received |
| Mode switch /intimate /secretary | SC-3 | Session state requires live user | Send /intimate, confirm mode, send /secretary, confirm revert |
| Photo appears in chat within 5 min | SC-4 | Multi-hop BullMQ + ComfyUI + watermark pipeline | In intimate mode, request photo, confirm delivery |
| Google Calendar event creation | SC-6a | Requires pre-authorized Google OAuth | Ask Ava to create a calendar event, confirm in Google Calendar |
| Web search completes | SC-6b | Requires Tavily API key wired in production | Ask Ava a factual question requiring search, confirm sourced reply |
| Auth pages render correctly | AUTH-01/02 | Browser visual check | Visit /login, /signup, /forgot-password |
| Landing page renders | LAND-01/02/03 | Browser visual check | Visit /, confirm CTA routes to signup |
| Billing portal redirects | SUBS-01/02/03/04/05 | Requires Stripe + browser | Visit /billing, confirm portal redirect |
| Admin dashboard accessible | ADMN-01 | Requires super-admin role | Visit /admin with operator account, confirm metrics visible |
| Email delivery for signup/magic-link | EMAI-01/02/03/04 | Requires inbox access | Sign up with real email, confirm receipt |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
