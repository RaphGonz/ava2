---
phase: 12
slug: admin-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (frontend)** | Vitest ^4.0.18 + @testing-library/react |
| **Framework (backend)** | pytest (existing test suite) |
| **Config file (frontend)** | `frontend/vitest.config.ts` |
| **Config file (backend)** | none — run from `backend/` directory |
| **Quick run command (frontend)** | `cd frontend && npx vitest run --reporter=verbose` |
| **Quick run command (backend)** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd frontend && npx vitest run && cd ../backend && python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run full suite: `cd frontend && npx vitest run && cd ../backend && python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | ADMN-03 | unit | `cd backend && python -m pytest tests/test_admin_access.py -x -q` | ❌ Wave 0 | ⬜ pending |
| 12-01-02 | 01 | 1 | ADMN-01, ADMN-03 | unit | `cd backend && python -m pytest tests/test_admin_access.py -x -q` | ❌ Wave 0 | ⬜ pending |
| 12-02-01 | 02 | 1 | ADMN-02 | unit | `cd backend && python -m pytest tests/test_admin_events.py -x -q` | ❌ Wave 0 | ⬜ pending |
| 12-02-02 | 02 | 1 | ADMN-02 | unit | `cd backend && python -m pytest tests/test_admin_events.py -x -q` | ❌ Wave 0 | ⬜ pending |
| 12-03-01 | 03 | 2 | ADMN-01, ADMN-03 | unit | `cd frontend && npx vitest run --reporter=verbose src/pages/AdminPage.test.tsx` | ❌ Wave 0 | ⬜ pending |
| 12-03-02 | 03 | 2 | ADMN-01, ADMN-03 | unit | `cd frontend && npx vitest run --reporter=verbose src/pages/AdminPage.test.tsx` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_admin_access.py` — stubs for ADMN-01, ADMN-03 (require_admin: 403 for non-admin, 200 for admin, 401 for unauthenticated)
- [ ] `backend/tests/test_admin_events.py` — stubs for ADMN-02 (usage event emit points mocked, correct call paths)
- [ ] `frontend/src/pages/AdminPage.test.tsx` — stubs for ADMN-01 (5 stat cards render), ADMN-03 (AdminRoute redirects non-admin to /chat)

*All three test files are created as Wave 0 tasks (task 1 of each plan).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GET /admin/metrics returns real data for 5 metrics | ADMN-01 | Requires live Supabase data (auth.users, subscriptions, usage_events) | Visit /admin as admin user; verify all 5 cards show non-null values drawn from real data |
| usage_events rows accumulate from real actions | ADMN-02 | Requires live DB writes from real chat/photo/mode-switch/subscription actions | Perform each action in production; check Supabase Dashboard → usage_events table for rows |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
