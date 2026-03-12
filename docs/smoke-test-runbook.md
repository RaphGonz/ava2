# Phase 13 Smoke Test Runbook — v1.1 Milestone Validation

**Date:** 2026-03-12
**Tester:** Raphael (operator)
**Production URL:** https://avasecret.org
**Runbook version:** 1.1

---

## Prerequisites (complete BEFORE running any scenario)

1. **Production server health check:** `curl -sf https://avasecret.org/health` must return `{"status":"ok"}`
2. **Confirm STRIPE_SECRET_KEY is set on VPS:** `ssh user@vps grep STRIPE_SECRET_KEY backend/.env` — must not be empty (if empty, SC-5 will give false 200 instead of 402)
3. **Confirm worker container is running:** `ssh user@vps docker compose ps` — `worker` status must be `running` (required for SC-4 photo delivery)
4. **Confirm operator Supabase admin role:** In Supabase Dashboard > Authentication > Users > find operator account > inspect `raw_app_meta_data` — must contain `"role": "super-admin"` (with hyphen, not underscore)
5. **Test account setup:**
   - **Subscribed test account:** operator's own account (has active subscription) — use for SC-1, SC-2, SC-3, SC-4, SC-6
   - **Unsubscribed test account:** a separate account with NO row in `subscriptions` table (or row with status != "active") — use for SC-5
6. **Google Calendar OAuth pre-authorization (required for SC-6a):** Log in as subscribed test account, visit `https://avasecret.org/auth/google/start`, complete OAuth flow, verify `google_calendar_tokens` row exists in Supabase for this user_id
7. **Mode state reset (prevent SC-3 cross-contamination):** Before SC-3, send `/secretary` in chat to ensure session starts in secretary mode

## Scenario Execution Order

Run scenarios in this order to minimize state side effects: **SC-1 → SC-2 → SC-3 → SC-4 → SC-5 (separate account) → SC-6**

---

## SC-1: Avatar Setup & Reference Image Pipeline

**Requirements covered:** INFRA-01, INFRA-02, INFRA-04, EMAI-01, EMAI-02, AUTH-01

**Steps:**
1. Open browser in incognito mode, navigate to https://avasecret.org
2. Click "Continue with Google" — verify Google OAuth login completes and redirects to /chat or avatar setup
   - AUTH-01 check: Google OAuth completed without error
3. Check inbox within 60 seconds — verify welcome email arrived (not spam)
   - EMAI-02 check: welcome email in inbox with correct sender/subject
4. Complete avatar setup form (name, age, personality) and click submit
5. Note start time. Every 30 seconds, call `GET /avatars/me` with the authenticated user's JWT and inspect `reference_image_url` in the JSON response (NOT the raw Supabase table view — the API rewrites storage path to signed https:// URL)
6. If `reference_image_url` is a full `https://` URL within 5 minutes: **SC-1 PASS**
7. If still null/storage-path after 5 minutes: **SC-1 FAIL** — run `docker compose logs worker --tail=50` on VPS to diagnose

**Email sub-checks** (complete while waiting for reference image):
- INFRA-01: App is reachable at https://avasecret.org (you just loaded it)
- INFRA-02: No certificate warning in browser; `curl -I http://avasecret.org` returns 301 redirect to HTTPS
- INFRA-03: `nmap -p 80,443,8000,5432 avasecret.org` — only 80 and 443 open (or check via shodan.io)

---

## SC-2: Secretary Mode Chat Reply

**Requirements covered:** INFRA-04 (OpenAI credential), AUTH-02

**Steps:**
1. Logged in as subscribed test account, navigate to /chat
2. Ensure you are in secretary mode (send `/secretary` if needed, observe "You're now in secretary mode" confirmation)
3. Send a simple factual question: "What is the capital of France?"
4. Verify: a coherent reply is received within 30 seconds
5. Auth check (do separately): Test forgot-password flow for a registered email — verify reset email arrives in inbox within 2 minutes
   - AUTH-02 check: reset link is functional (clicking it loads ResetPasswordPage)

---

## SC-3: Mode Switching (Session Isolation)

**Requirements covered:** INFRA-04 (session isolation logic)

**Steps:**
1. Confirm starting state: in secretary mode (send `/secretary` if needed)
2. Send `/intimate` — observe: reply must contain mode switch confirmation message ("intimate mode" or similar)
   - Record the exact response text as evidence
3. Send `/secretary` — observe: reply must contain mode switch confirmation back to secretary
   - Record the exact response text as evidence
4. Send one more message in secretary mode — verify coherent secretary-mode reply (not intimate-mode behavior)

**PASS criteria:** Both switch messages observed, no cross-mode contamination in replies

**Pitfall:** If `/intimate` produces no switch message, the session was already in intimate mode (from a prior test). Send `/secretary` first to reset, then retry.

---

## SC-4: BullMQ Photo Delivery in Intimate Mode

**Requirements covered:** INFRA-04 (ComfyUI Cloud credential, BullMQ worker)

**Steps:**
1. Ensure session is in intimate mode (send `/intimate`)
2. Send a message that triggers a photo: "send me a photo" or similar
3. Observe: an immediate placeholder reply in chat ("generating your photo" or similar)
4. Note start time. Every 30 seconds, refresh the chat and check if an actual image appears (not just the placeholder text)
5. If image appears in chat within 5 minutes: **SC-4 PASS** — take a screenshot as evidence
6. If no image after 5 minutes: **SC-4 FAIL** — run on VPS:
   - `docker compose ps` — confirm worker container is running (not exited)
   - `docker compose logs worker --tail=50` — look for job processing logs or error messages

---

## SC-5: Stripe Paywall Active (Unsubscribed Account)

**Requirements covered:** SUBS-01, SUBS-02, SUBS-03, SUBS-04, SUBS-05, ADMN-03

**Steps:**
1. Run automated tests: `cd backend && SMOKE_UNSUBSCRIBED_JWT=<jwt> SMOKE_REGULAR_USER_JWT=<jwt> python -m pytest tests/test_smoke_paywall.py -x -v`
   - Obtain SMOKE_UNSUBSCRIBED_JWT: log in to production as unsubscribed user, copy access_token from DevTools > Application > Local Storage > sb-\*-auth-token
   - Obtain SMOKE_REGULAR_USER_JWT: log in as any non-admin production user
2. All 3 tests must PASS: 401 (no auth), 402 (unsubscribed), 403 (non-admin admin route)

**Billing page checks** (manual, logged in as subscribed user):
3. Navigate to /billing — verify: plan name, status, and next billing date visible (SUBS-01)
4. Click "Manage billing" or "Update payment method" — verify: Stripe Customer Portal opens (SUBS-02)
5. Start cancellation flow — verify: exit survey appears (SUBS-04); "Skip and cancel" option is present (SUBS-05); full flow completes in ≤3 clicks from Cancel link (SUBS-05)
6. After cancellation: verify subscription shows cancel_at_period_end=True and access is retained until period end date (SUBS-03)

**EMAI-03 receipt email check:**
7. To verify EMAI-03, inspect the most recent `invoice.paid` webhook event using one of these paths:
   - **Resend dashboard:** Log in to resend.com -> Emails -> filter by "receipt" or the subscription receipt template — verify the most recent receipt email was delivered to the expected address with no bounce.
   - **Alternative — Supabase webhook logs:** Supabase Dashboard -> Database -> Webhooks or Functions -> inspect logs for the most recent `invoice.paid` event from Stripe, confirm the receipt email trigger fired without error.
   - **Alternative — Stripe test-mode webhook replay:** In Stripe Dashboard -> Developers -> Webhooks -> select the production webhook endpoint -> "Send test event" -> select `invoice.paid` event type -> click "Send". Then check the inbox of the test subscribed user for a receipt email within 60 seconds.
   - EMAI-03 PASS: receipt email delivered (found in Resend logs or inbox)
   - EMAI-03 FAIL: no email found in Resend logs and no recent `invoice.paid` event in webhook logs

**Note:** Cancellation test should use a test account, not the operator's primary subscription.

---

## SC-6: Secretary Skills — Calendar & Web Search

**Requirements covered:** INFRA-04 (Tavily credential, Google Calendar tokens)

**Steps:**
1. Ensure Google Calendar is pre-authorized for the test user (SC-6a prerequisite — see Prerequisites step 6)
2. In secretary mode, request a calendar event: "Schedule a meeting with John tomorrow at 2pm"
3. Observe: Ava confirms the event OR asks for confirmation if there's a calendar conflict
4. If confirmation requested, reply "yes" and verify event is created
5. Check Google Calendar directly — event should appear for tomorrow at 2pm
   - SC-6a PASS: event created in Google Calendar
   - SC-6a FAIL: chat reply contains "To use calendar features, connect your Google Calendar" → re-authorize OAuth
6. In secretary mode, ask a web search question: "What are the latest AI news today?"
7. Observe: Ava returns a coherent answer with search-sourced content (not just "I don't know")
   - SC-6b PASS: relevant web search result returned in reply

**Additional landing page checks** (manual — browser, unauthenticated):
8. Sign out, navigate to https://avasecret.org — verify: hero section, features section, pricing section all visible (LAND-01)
9. Click any CTA button — verify: navigates to /signup without intermediate pages (LAND-02)
10. Scan visible page text — verify: no words "intimate", "explicit", "NSFW", "adult" appear anywhere (LAND-03)

---

## Evidence Table

Fill in this table as you execute each scenario. Commit the completed table alongside this runbook.

| SC | Criterion | Status | Evidence | Timestamp |
|----|-----------|--------|----------|-----------|
| SC-1 | reference_image_url non-null https:// URL within 5 min | PASS | https:// URL returned from GET /avatars/me within 5 min | 2026-03-12 |
| SC-2 | Secretary mode: coherent reply received | PASS | Coherent reply received in secretary mode | 2026-03-12 |
| SC-3a | /intimate produces mode switch message | PASS | Mode switch confirmation message observed | 2026-03-12 |
| SC-3b | /secretary produces mode switch back | PASS | Mode switch back confirmation message observed | 2026-03-12 |
| SC-4 | Photo appears in chat within 5 min | PASS | Image rendered in chat bubble (bug fixed: was showing raw URL, now renders as img) | 2026-03-12 |
| SC-5a | POST /chat no auth -> 401 | PASS | pytest: test_unauthed_chat_returns_401 PASSED | 2026-03-12 |
| SC-5b | POST /chat unsubscribed -> 402 | PASS | pytest: test_unsubscribed_chat_returns_402 PASSED | 2026-03-12 |
| SC-5c | GET /admin/metrics non-admin -> 403 | PASS | pytest: test_non_admin_gets_403 PASSED | 2026-03-12 |
| SC-6a | Calendar event created in Google Calendar | PASS | Calendar event created and confirmed in Google Calendar | 2026-03-12 |
| SC-6b | Web search returns content-rich reply | PASS | Web search reply with sourced content returned | 2026-03-12 |
| INFRA-01 | https://avasecret.org loads without error | PASS | curl: {"status":"ok"} | 2026-03-12 |
| INFRA-02 | HTTP -> HTTPS redirect (301), no cert warning | PASS | Confirmed no cert warning, HTTPS enforced | 2026-03-12 |
| INFRA-03 | Only ports 80/443 reachable | PASS | Confirmed by operator | 2026-03-12 |
| AUTH-01 | Google OAuth sign-in completes | PASS | Google OAuth completed, redirected to /chat | 2026-03-12 |
| AUTH-02 | Forgot-password email arrives + link works | PASS | Reset email arrived in inbox, link functional | 2026-03-12 |
| EMAI-02 | Welcome email in inbox within 60s | PASS | Welcome email received in inbox | 2026-03-12 |
| EMAI-03 | Receipt email confirmed via Resend logs or webhook replay | PASS | Receipt email confirmed (real subscription taken during test) | 2026-03-12 |
| EMAI-04 | Cancellation email in inbox within 60s | PASS | Cancellation confirmation email received | 2026-03-12 |
| LAND-01 | Hero + features + pricing sections visible | PASS | Hero, features, pricing sections all visible | 2026-03-12 |
| LAND-02 | CTA button -> /signup (no intermediate page) | PASS | CTA navigates directly to /signup | 2026-03-12 |
| LAND-03 | No prohibited copy on landing page | PASS | No flagged terms found on landing page | 2026-03-12 |
| SUBS-01 | Billing page shows plan/status/next billing date | PASS | Plan name, status, next billing date visible on /billing | 2026-03-12 |
| SUBS-02 | Stripe Customer Portal opens | PASS | Stripe Customer Portal loaded successfully | 2026-03-12 |
| SUBS-03 | cancel_at_period_end=True after cancellation | PASS | cancel_at_period_end=True confirmed, access retained | 2026-03-12 |
| SUBS-04 | Exit survey appears before cancellation | PASS | Exit survey displayed before cancellation completes | 2026-03-12 |
| SUBS-05 | Skip option present, ≤3 clicks to cancel | PASS | Skip option present, cancelled in 3 clicks | 2026-03-12 |
| ADMN-01 | /admin/metrics shows 5 metrics with real data | PASS | 5 metrics with real data visible on /admin | 2026-03-12 |
| ADMN-02 | usage_events has all 4 event types | PASS | pytest: test_all_required_event_types_present PASSED (message_sent, photo_generated, mode_switch, subscription_created) | 2026-03-12 |
| ADMN-03 | /admin/metrics non-admin -> 403 | PASS | pytest: test_non_admin_gets_403 PASSED | 2026-03-12 |

---

## Admin Dashboard Check (ADMN-01)

**Steps:**
1. Log in as operator (with super-admin role in app_metadata)
2. Navigate to /admin
3. Verify all 5 metrics are visible with non-zero values: active users (7-day), messages sent, photos generated, active subscriptions, new signups
4. Run automated test: `cd backend && SMOKE_ADMIN_JWT=<jwt> python -m pytest tests/test_smoke_admin.py -x -v`
   - Obtain SMOKE_ADMIN_JWT: log in as the operator account, copy access_token from DevTools > Application > Local Storage > sb-\*-auth-token -> access_token
5. Run `cd backend && python -m pytest tests/test_smoke_usage_events.py -x -v` to verify ADMN-02

---

## Automated Test Block

Run all smoke automation before declaring milestone complete:

```bash
# Pre-flight: confirm server alive
curl -sf https://avasecret.org/health && echo "PASS: server alive" || echo "FAIL: server unreachable"

# Paywall + admin access control (set env vars first)
cd backend
SMOKE_UNSUBSCRIBED_JWT="<paste JWT here>" \
SMOKE_REGULAR_USER_JWT="<paste JWT here>" \
python -m pytest tests/test_smoke_paywall.py -x -v

# Admin metrics (ADMN-01)
SMOKE_ADMIN_JWT="<paste admin JWT here>" \
python -m pytest tests/test_smoke_admin.py -x -v

# Usage events (runs from backend/ with production DB configured in .env)
python -m pytest tests/test_smoke_usage_events.py -x -v
```

---

## Milestone Declaration

The v1.1 milestone is SHIPPED when:
- [x] All rows in the Evidence Table above are marked PASS
- [x] All automated pytest smoke tests PASS (not SKIP)
- [x] Completed evidence table committed to this file in the repo
- [x] ROADMAP.md Phase 13 marked complete

## Milestone Declaration

v1.1 Launch Ready milestone **SHIPPED** — 2026-03-12. All 28 criteria PASS.

**Bugs found and fixed during validation:**
- `ChatBubble.tsx`: `[PHOTO]url[/PHOTO]` token rendered as plain text instead of `<img>` — fixed (commit 9c86a54)
- `web_chat.py`: signed photo URLs regenerated on every 3s poll causing image flicker — fixed with in-memory cache (commit 9162b54)

---

*Runbook version: 1.1 — updated Phase 13 Plan 01 revision (added ADMN-01 automated test, EMAI-03 Resend/webhook verification path)*
*Production URL: https://avasecret.org*
