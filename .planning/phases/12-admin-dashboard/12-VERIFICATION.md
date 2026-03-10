---
phase: 12-admin-dashboard
verified: 2026-03-10T00:00:00Z
status: human_needed
score: 9/9 must-haves verified
re_verification: false
human_verification:
  - test: "Sign in as a Supabase user with user_metadata.is_admin=true and visit /admin in a browser"
    expected: "Page renders 'Admin Dashboard' title, a 'Last updated: HH:MM' timestamp, and 5 stat cards (Active Users, Messages Sent, Photos Generated, Active Subscriptions, New Signups) each with 7d / 30d / All time rows showing real values from the database"
    why_human: "Requires live Supabase connection with real usage_events rows, auth.users records, and subscriptions rows — cannot be verified from static code inspection alone"
  - test: "Sign in as a non-admin user and navigate to /admin"
    expected: "Silent redirect to /chat with no 403 error message, no metrics data visible, no flash of admin content"
    why_human: "Real browser navigation required to confirm silent redirect behavior end-to-end"
  - test: "Perform a chat message exchange in production, then open Supabase Dashboard > Table Editor > usage_events"
    expected: "A row with event_type='message_sent' and the correct user_id appears"
    why_human: "Verifies live DB write from chat.py emission point — requires real user action against a live Supabase instance"
  - test: "Complete a Stripe subscription checkout in production, then check usage_events table"
    expected: "A row with event_type='subscription_created' appears after activate_subscription() completes"
    why_human: "Requires live Stripe webhook delivery and database write — no static verification possible"
---

# Phase 12: Admin Dashboard Verification Report

**Phase Goal:** The operator can view key product metrics from a protected /admin page, with usage events accumulating from earlier phases
**Verified:** 2026-03-10
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Success Criteria from ROADMAP.md

| # | Success Criterion | Status | Evidence |
|---|-------------------|--------|----------|
| 1 | Operator with admin role visiting /admin sees active users, messages sent, photos generated, active subscriptions, new signups drawn from real data | ? HUMAN NEEDED | All code is wired correctly; real-data display requires live DB |
| 2 | Regular user navigating to /admin receives a 403 response — no metrics visible, no data leaked | ? HUMAN NEEDED | AdminRoute guard verified in code and tests; end-to-end redirect needs browser confirmation |
| 3 | usage_events table contains rows for message_sent, photo_generated, mode_switch, subscription_created — emission points wired | ? HUMAN NEEDED | All 4 emission points confirmed in source; actual row accumulation requires live environment |

**Note:** All automated checks below pass. The human_needed status is because all three ROADMAP success criteria require live database/browser verification — the code is fully wired and substantive.

---

### Observable Truths — Automated

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /admin/metrics returns 5 metrics (active_users, messages_sent, photos_generated, active_subscriptions, new_signups) each with d7/d30/all fields | VERIFIED | `admin.py:142-204` — `@router.get("/metrics")` builds and returns all 5 keys with d7/d30/all structure |
| 2 | require_admin raises 403 for non-admin users (missing/false is_admin in user_metadata) | VERIFIED | `admin.py:31-44` — `(user.user_metadata or {}).get("is_admin", False)` raises HTTP 403; 4 pytest tests in `test_admin_access.py` all cover this path |
| 3 | require_admin reads user_metadata (not app_metadata) from Supabase JWT | VERIFIED | `admin.py:38` — `user.user_metadata or {}` explicitly; no reference to `app_metadata` anywhere in admin.py |
| 4 | Admin router is registered in main.py | VERIFIED | `main.py:14,101` — `from app.routers import admin` and `app.include_router(admin.router)` |
| 5 | message_sent emit fires at end of normal LLM/skill flow in chat.py | VERIFIED | `chat.py:393-401` — try/except insert with event_type="message_sent" placed between final append_message calls and `return reply` |
| 6 | mode_switch emit fires at all 3 actual switch paths (not already-in-mode) | VERIFIED | `chat.py:171-181` (pending clarification path), `231-242` (custom phrase path), `263-274` (exact/fuzzy detection path) — none adjacent to ALREADY_INTIMATE_MSG / ALREADY_SECRETARY_MSG returns |
| 7 | photo_generated emit fires after audit_log write in processor.py (both preserved) | VERIFIED | `processor.py:162-192` — audit_log at lines 165-181, usage_events insert at 183-192 as Step 7b; comment explicitly states both are independent |
| 8 | subscription_created emit fires in checkout.session.completed handler in billing.py | VERIFIED | `billing.py:190-199` — try/except insert after `activate_subscription()` completes |
| 9 | /admin route in App.tsx is wrapped in AdminRoute guard; no navigation link to /admin exists in other pages | VERIFIED | `App.tsx:160-167` — Route path="/admin" wrapped in `<AdminRoute>`; grep across all frontend pages found no href/Link/to pointing to /admin outside of App.tsx route definition |

**Score:** 9/9 truths verified (automated)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/routers/admin.py` | require_admin dependency + GET /admin/metrics endpoint | VERIFIED | 209 lines; exports `router` and `require_admin`; full metrics implementation with 5 metrics and 3 time windows |
| `backend/tests/test_admin_access.py` | pytest tests for require_admin access control | VERIFIED | 4 tests: allows_admin_true, blocks_non_admin, blocks_admin_false, handles_null_metadata |
| `backend/tests/test_admin_events.py` | pytest tests for 4 usage event emission paths | VERIFIED | 7 source-inspection tests: photo_generated, audit_log regression, message_sent, mode_switch, mode_switch-not-on-already-in-mode, subscription_created, both-subscription-events |
| `frontend/src/api/admin.ts` | getAdminMetrics() API function with AdminMetrics type | VERIFIED | Exports MetricWindow, AdminMetrics types and getAdminMetrics(token); fetches /admin/metrics with Bearer auth |
| `frontend/src/pages/AdminPage.tsx` | Admin dashboard with 5 metric cards and AdminRoute guard | VERIFIED | Named export AdminRoute (JWT user_metadata.is_admin check), default export AdminPage with 5 StatCards, loading state, error state, manual refresh |
| `frontend/src/pages/AdminPage.test.tsx` | Vitest tests for access control and card rendering | VERIFIED | 4 tests: redirect-to-login, redirect-to-chat (non-admin), renders-children (admin), renders-5-metric-titles |
| `frontend/src/App.tsx` | /admin route wired with AdminRoute guard | VERIFIED | Route path="/admin" wrapped in AdminRoute at lines 160-167 |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/routers/admin.py` | `backend/app/dependencies.py:get_current_user` | `Depends(get_current_user)` inside require_admin | WIRED | `admin.py:31` — `async def require_admin(user=Depends(get_current_user))` |
| `backend/app/routers/admin.py` | `backend/app/database.py:supabase_admin` | supabase_admin.auth.admin.list_users() and PostgREST queries | WIRED | `admin.py:23` — `from app.database import supabase_admin`; used at lines 57-64, 70-76, 86-88 |
| `backend/app/main.py` | `backend/app/routers/admin.py` | app.include_router(admin.router) | WIRED | `main.py:14` — import; `main.py:101` — include_router call |
| `backend/app/services/chat.py` | usage_events table | event_type="message_sent" insert after reply returned | WIRED | `chat.py:393-401` — try/except insert with correct event_type |
| `backend/app/services/chat.py` | usage_events table | event_type="mode_switch" at all 3 switch paths | WIRED | Lines 171-181, 231-242, 263-274 — 3 separate try/except blocks, each after switch_mode() call |
| `backend/app/services/jobs/processor.py` | usage_events table | event_type="photo_generated" after audit_log write | WIRED | `processor.py:183-192` — Step 7b insert; audit_log at 165-181 preserved |
| `backend/app/routers/billing.py` | usage_events table | event_type="subscription_created" after activate_subscription() | WIRED | `billing.py:190-199` — insert in checkout.session.completed branch |
| `frontend/src/App.tsx` | `frontend/src/pages/AdminPage.tsx` | Route path="/admin" wrapped in AdminRoute | WIRED | `App.tsx:160-167` — AdminRoute wraps AdminPage; both imported from `./pages/AdminPage` |
| `frontend/src/pages/AdminPage.tsx` | `frontend/src/api/admin.ts` | useQuery queryFn: () => getAdminMetrics(token) | WIRED | `AdminPage.tsx:57` — `queryFn: () => getAdminMetrics(token)` |
| `frontend/src/api/admin.ts` | GET /admin/metrics | fetch('/admin/metrics', { headers: { Authorization: Bearer token } }) | WIRED | `admin.ts:23` — `fetch('/admin/metrics', { headers: { Authorization: \`Bearer ${token}\` } })` |

---

## Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|----------|
| ADMN-01 | 12-01, 12-03 | Operator can view key metrics: active users (7-day), messages sent, photos generated, active subscriptions, new signups | SATISFIED | Backend `GET /admin/metrics` returns all 5 metrics with d7/d30/all windows; frontend AdminPage renders 5 stat cards |
| ADMN-02 | 12-02 | Usage events logged to usage_events table (message_sent, photo_generated, mode_switch, subscription_created) | SATISFIED | All 4 emission points wired with try/except fire-and-forget pattern: chat.py (message_sent + mode_switch), processor.py (photo_generated), billing.py (subscription_created) |
| ADMN-03 | 12-01, 12-03 | /admin route restricted to admin role — regular users receive 403 | SATISFIED | Backend require_admin dependency raises HTTP 403 when user_metadata.is_admin != true; frontend AdminRoute redirects non-admins to /chat silently |

**Orphaned requirements (REQUIREMENTS.md Phase 12 entries not in any plan):** None — all 3 ADMN IDs appear in plans 01, 02, and 03.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/routers/admin.py` | 82 | `# TODO: paginate for >1000 users (list_users() returns max 1000 by default)` | INFO | Known limitation at current scale; acknowledged in plan decisions; does not affect correctness for sub-1000 user counts |

No blockers or warnings. The single TODO is a documented known limitation deferred intentionally — the comment itself serves as the future work marker.

---

## Human Verification Required

### 1. Admin dashboard renders real data

**Test:** Sign in as a Supabase user with `user_metadata.is_admin=true` and visit `/admin` in a browser.
**Expected:** Page renders "Admin Dashboard" title, a "Last updated: HH:MM" timestamp, and all 5 stat cards showing non-zero values where real activity has occurred.
**Why human:** Requires a live Supabase instance with actual auth.users records, subscriptions rows, and usage_events rows. Static code inspection confirms the queries are correct but cannot verify the data flows end-to-end.

### 2. Non-admin redirect is silent (no 403 shown)

**Test:** Sign in as a regular (non-admin) user and navigate directly to `/admin`.
**Expected:** Silent redirect to `/chat` with no flash of admin content, no error message, no 403 page.
**Why human:** AdminRoute guard is verified in Vitest tests but the end-to-end redirect behavior (no flash, correct URL in address bar) requires browser confirmation.

### 3. message_sent event accumulates in production

**Test:** Send several chat messages in the production web app as a normal user, then open Supabase Dashboard > Table Editor > usage_events.
**Expected:** Rows with `event_type='message_sent'` appear for each LLM/skill reply delivered (not for mode switch returns or crisis returns).
**Why human:** Requires live Supabase write from a real chat session — cannot be verified without a running backend connected to the database.

### 4. subscription_created event fires on Stripe checkout

**Test:** Complete a Stripe checkout session in production (or use Stripe's test mode with a webhook forward), then check the usage_events table.
**Expected:** A row with `event_type='subscription_created'` and the correct `user_id` and `customer_id` appears after the checkout.session.completed webhook is processed.
**Why human:** Requires Stripe webhook delivery to the live backend — cannot be simulated from code inspection.

---

## Gaps Summary

No gaps found. All 9 automated truths pass, all artifacts exist and are substantive, all key links are wired, all 3 requirement IDs are satisfied by the implemented code.

The human_needed status reflects that the three ROADMAP success criteria are stated in terms of observable runtime behavior ("sees real data", "contains rows") which cannot be verified from static code analysis alone. The code correctness supporting those behaviors is fully verified.

---

_Verified: 2026-03-10_
_Verifier: Claude (gsd-verifier)_
