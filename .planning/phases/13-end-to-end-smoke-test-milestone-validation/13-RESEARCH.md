# Phase 13: End-to-End Smoke Test & Milestone Validation — Research

**Researched:** 2026-03-10
**Domain:** Production smoke testing — manual verification scripts, automated paywall checks, and milestone gate criteria
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | App deployed to production VPS and running | SC-1: new user signup flow depends on app being reachable |
| INFRA-02 | All traffic served over HTTPS with auto-renewal (Caddy) | SC-1: ComfyUI callback requires HTTPS; symptom check covers cert validity |
| INFRA-03 | Firewall — only ports 80 and 443 exposed | Verified as part of deployment check in each scenario |
| INFRA-04 | All production API credentials wired and verified | Each success criterion directly exercises one or more credentials |
| EMAI-01 | Email DNS (SPF/DKIM/DMARC) configured | SC-1: welcome email delivery is part of signup scenario |
| EMAI-02 | Welcome email on signup | SC-1: new user signup scenario confirms email arrives |
| EMAI-03 | Receipt email after payment | Covered by Stripe checkout scenario in SC-5 area |
| EMAI-04 | Confirmation email after cancellation | Manual check item in billing scenario |
| AUTH-01 | Google Sign-In (Supabase PKCE) | SC-1: signup may use Google OAuth path |
| AUTH-02 | Forgot-password email link | Separate manual check item in auth scenario |
| LAND-01 | Landing page hero + features + pricing | Manual smoke: unauthenticated visitor check |
| LAND-02 | CTA reaches signup flow | Manual smoke: CTA button routing check |
| LAND-03 | No prohibited copy ("intimate", "explicit", NSFW) | Copy audit step in landing page scenario |
| SUBS-01 | Billing page shows plan/status/next billing date | Manual smoke: billing page inspection |
| SUBS-02 | Stripe Customer Portal accessible | Manual smoke: portal redirect works |
| SUBS-03 | Cancel from billing page | Manual smoke: cancellation flow |
| SUBS-04 | Exit survey before cancellation | Manual smoke: survey appears |
| SUBS-05 | Survey skippable, ≤3 clicks | Manual smoke: skip path verified |
| ADMN-01 | /admin shows 5 key metrics | SC-6 area: admin dashboard metrics are live |
| ADMN-02 | usage_events table accumulates 4 event types | Automated check: query usage_events via psql/Supabase |
| ADMN-03 | /admin restricted to admin role (403 for non-admin) | SC-5: unsubscribed user gets 402; admin test covers 403 |
</phase_requirements>

---

## Summary

Phase 13 is a milestone gate, not a feature phase. Its entire purpose is to run every v1.1 success criterion against the live production environment and record pass/fail evidence before the milestone is declared shipped. The six success criteria span three asynchronous pipelines (ComfyUI reference image, BullMQ photo delivery, email delivery) plus synchronous HTTP contracts (paywall 402, mode detection, secretary skills). None of these can be verified by unit tests alone — they require real credentials, real network, and real background workers running.

The primary challenge is that several criteria have timing constraints (reference image within 5 minutes, photo in chat within 5 minutes). These must be structured as polling loops with explicit timeouts, not fire-and-forget checks. The planner must produce a runbook that a human can execute step-by-step and record the outcome of each criterion unambiguously.

The secondary challenge is credential isolation: the smoke test must use a *real production* test account (not a dev account), a *real active Stripe subscription* (or a Stripe test-mode account on the production server), and Google Calendar must be authorized for the skills check. The runbook must document account setup prerequisites before any scenario is attempted.

**Primary recommendation:** Structure Phase 13 as a two-plan phase: Plan 13-01 creates an automated paywall verification script (the only criterion amenable to full automation) and a structured human runbook document; Plan 13-02 executes the full runbook against production, records evidence (timestamps, screenshots, Supabase row values), and declares milestone shipped or blocked with a failure report.

---

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| pytest + pytest-asyncio | >=7.0 / >=0.21 (already in requirements.txt) | Automated 402 paywall check, usage_events query | Already project test framework; zero new deps |
| httpx | >=0.27 (already in requirements.txt) | HTTP smoke requests against production API | Already project HTTP client; handles async cleanly |
| Supabase service role key | n/a (existing credential) | Query usage_events, avatars tables for evidence | Avoids writing a second API layer; direct DB read |
| curl / browser DevTools | n/a (human tools) | Verify HTTPS redirect, inspect response headers | Industry-standard smoke test tools, no deps |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| Stripe test-mode | n/a | Simulate subscription activation without real card | When testing paywall on production without charging |
| Supabase Dashboard SQL editor | n/a | Inspect usage_events, avatars rows directly | Faster than scripting DB checks for one-off validation |
| mail-tester.com or inbox inspection | n/a | Confirm welcome/receipt emails land in inbox | Email delivery is not verifiable via API alone |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Human runbook for async scenarios | Playwright E2E suite | Playwright would require a full browser automation setup that doesn't exist in this project; overkill for a one-time milestone gate |
| Direct Supabase query for usage_events | Admin API GET /admin/metrics | Admin metrics endpoint is the correct production check; Supabase direct query is the fallback if admin account not ready |

**No new packages to install** — all automation uses existing project dependencies.

---

## Architecture Patterns

### Recommended Phase Structure
```
.planning/phases/13-end-to-end-smoke-test-milestone-validation/
├── 13-01-PLAN.md   # Produce: automated paywall script + human runbook document
├── 13-02-PLAN.md   # Execute: run runbook against production, record evidence, declare milestone
```

The runbook itself lives in the repo as a Markdown document (e.g. `docs/smoke-test-runbook.md` or inline in the plan) so evidence can be committed alongside the checklist.

### Pattern 1: Automated Paywall Check (SC-5)
**What:** pytest script that hits `POST /chat` with no auth header, expects 401; then with a valid JWT of a user with no active subscription, expects 402; then confirms that `stripe_secret_key` is set (not empty) in production.
**When to use:** The only criterion that is fully automatable without live human interaction.

```python
# Source: project codebase — dependencies.py require_active_subscription pattern
import pytest
import httpx

PROD_BASE = "https://avasecret.org"  # production base URL

@pytest.mark.asyncio
async def test_paywall_unauthenticated():
    """No auth header -> 401 (bearer scheme enforcement)."""
    async with httpx.AsyncClient(base_url=PROD_BASE) as client:
        r = await client.post("/chat", json={"text": "hello"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_paywall_no_subscription(unsubscribed_user_jwt: str):
    """Valid JWT, no active subscription -> 402."""
    async with httpx.AsyncClient(
        base_url=PROD_BASE,
        headers={"Authorization": f"Bearer {unsubscribed_user_jwt}"}
    ) as client:
        r = await client.post("/chat", json={"text": "hello"})
    assert r.status_code == 402
    assert r.json()["detail"] == "Subscription required. Visit /subscribe to activate."
```

**Critical:** The `unsubscribed_user_jwt` fixture requires a real Supabase user with no row in the `subscriptions` table (or a row with `status != "active"`). This JWT must be obtained from the production Supabase instance, not a local dev instance.

### Pattern 2: Polling Loop for Async Criteria (SC-1, SC-4)
**What:** Reference image (SC-1) and BullMQ photo (SC-4) both complete asynchronously within 5 minutes. The runbook must instruct the tester to poll and record when the condition becomes true.

```
SC-1 polling procedure:
1. Complete avatar setup (POST /avatars/me, POST /avatars/me/reference-image)
2. Note start time
3. Every 30 seconds: GET /avatars/me and check reference_image_url != null
4. If truthy within 5 minutes: PASS — record timestamp and URL value
5. If still null after 5 minutes: FAIL — record backend logs for BG_TASK steps
```

**Critical check:** The `reference_image_url` in the Supabase row will be a storage path (e.g. `{user_id}/reference.jpg`), not an HTTP URL. GET /avatars/me rewrites it to a signed URL at read time. The runbook must verify the API response contains an `https://` URL, not just check the raw DB column.

### Pattern 3: Structured Runbook with Pass/Fail Evidence Table
**What:** Each success criterion gets a row in an evidence table the tester fills in as they go.

```markdown
| SC | Criterion | Status | Evidence | Timestamp |
|----|-----------|--------|----------|-----------|
| SC-1 | reference_image_url non-null within 5 min | PASS/FAIL | [URL or "null after 5 min"] | HH:MM |
| SC-2 | Secretary mode reply received | PASS/FAIL | [reply excerpt] | HH:MM |
| SC-3 | /intimate → /secretary mode switch works | PASS/FAIL | ["Switched to secretary mode" response] | HH:MM |
| SC-4 | Photo appears in chat within 5 min | PASS/FAIL | [screenshot filename] | HH:MM |
| SC-5 | Unsubscribed POST /chat returns 402 | PASS/FAIL | [curl output or test run] | HH:MM |
| SC-6a | Calendar event created without error | PASS/FAIL | [Google Calendar event URL] | HH:MM |
| SC-6b | Web search completes without error | PASS/FAIL | [search result excerpt] | HH:MM |
```

### Anti-Patterns to Avoid

- **Declaring "complete" based on unit tests only:** Unit tests mock all external services. SC-1 through SC-4 and SC-6 can only pass with real API credentials in production. Never accept a green unit test suite as evidence for these criteria.
- **Reusing dev Supabase instance for production checks:** The `supabase_url` in production `.env` differs from local dev. Smoke test scripts must target production URLs explicitly (use env var or hardcoded production base).
- **Testing paywall bypass path:** `require_active_subscription` has a dev bypass: `if not settings.stripe_secret_key: return user`. On production, `STRIPE_SECRET_KEY` must be set. SC-5 only proves the paywall is active if `stripe_secret_key` is confirmed non-empty in production `.env`. Add a setup check: `curl https://avasecret.org/health` and verify the server is live, then confirm via Supabase that the subscription table exists.
- **SC-6 calendar test without OAuth token:** Google Calendar requires `google_calendar_tokens` to exist in Supabase for the test user. The tester must complete OAuth flow at `GET /auth/google/start` before the calendar skill test — document this as a prerequisite step.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email delivery verification | Custom SMTP listener | Inbox inspection (Gmail/Resend logs) | Email delivery requires DNS propagation and real MX; a test listener won't prove production email lands in inbox |
| Stripe subscription activation in tests | Fake webhook trigger | Stripe Dashboard test-mode checkout or existing test user with active sub | Stripe webhook signature validation blocks fake triggers against production |
| Photo-in-chat assertion | Custom polling bot | Human observer + browser DevTools Network tab | Chat photo delivery via BullMQ + storage sign URL is multi-hop; human observation confirms end-to-end delivery chain including frontend rendering |

**Key insight:** For a one-time milestone gate, human-executed runbook with recorded evidence is more reliable than a brittle automation suite that would need to mock nothing while hitting production.

---

## Common Pitfalls

### Pitfall 1: require_active_subscription Dev Bypass in Production
**What goes wrong:** SC-5 test passes (402 returned) but only because the test user is unsubscribed, not because the paywall is actually wired. Worse: if `STRIPE_SECRET_KEY` is empty in production `.env`, ALL users bypass the paywall and get 200.
**Why it happens:** `require_active_subscription` in `dependencies.py` has `if not settings.stripe_secret_key: return user`. This is intentional for local dev but catastrophic if the production secret key is missing.
**How to avoid:** Before running SC-5, confirm `STRIPE_SECRET_KEY` is set on the production VPS: `ssh user@vps grep STRIPE_SECRET_KEY backend/.env`. Then test with an unsubscribed user.
**Warning signs:** SC-5 test shows 200 instead of 402 → immediately check STRIPE_SECRET_KEY on VPS.

### Pitfall 2: reference_image_url Storage Path vs Signed URL
**What goes wrong:** Tester queries Supabase directly and sees `reference_image_url = "abc123/reference.jpg"` and marks SC-1 PASS. But the frontend shows a broken image.
**Why it happens:** The DB stores a raw storage path. GET /avatars/me rewrites it to a signed URL at read time. The test must verify the API response (not the raw DB value) contains an `https://` URL.
**How to avoid:** SC-1 check must call `GET /avatars/me` via the API and inspect `reference_image_url` in the JSON response — not the Supabase Dashboard table view.
**Warning signs:** Image shows in API response but is a non-URL string.

### Pitfall 3: BullMQ Worker Not Running (SC-4 silent failure)
**What goes wrong:** Asking for a photo in intimate mode gets a placeholder reply but no actual photo appears in chat after 5 minutes.
**Why it happens:** The BullMQ worker (`worker_main.py`) runs as a separate Docker container (`worker` service in docker-compose.yml). If it crashed or was never started, jobs sit in the Redis queue forever.
**How to avoid:** Before SC-4, confirm worker is running: `docker compose ps` on VPS — `worker` container status must be `running`, not `exited`.
**Warning signs:** `docker compose logs worker` shows no output or shows repeated crash restarts.

### Pitfall 4: Google Calendar OAuth Not Pre-Authorized for Test User (SC-6a)
**What goes wrong:** Calendar create test fails with "To use calendar features, connect your Google Calendar: {url}" response.
**Why it happens:** Google Calendar requires completing OAuth at `GET /auth/google/start` and storing tokens in `google_calendar_tokens` table. The smoke test user must have done this before the skills check.
**How to avoid:** Add SC-6 prerequisite: "Confirm test user has Google Calendar connected. Visit GET /auth/google/start if not. Verify `google_calendar_tokens` row exists in Supabase for this user_id."
**Warning signs:** Chat reply contains the NOT_CONNECTED_MSG template (`"To use calendar features, connect your Google Calendar"`).

### Pitfall 5: Session State Cross-Contamination (SC-3)
**What goes wrong:** Mode switch test fails because a previous test left the session in intimate mode and the expected "You're now in secretary mode" switch message doesn't appear.
**Why it happens:** `SessionStore` is in-memory and persists across requests for the same user. If SC-2 (secretary mode chat) and SC-3 (mode switch) use the same test user, the session state from SC-2 carries over.
**How to avoid:** SC-3 must start from a known state. The runbook should instruct the tester to send `/secretary` first (to ensure starting in secretary mode), then `/intimate`, observe the switch message, then `/secretary` again. Record both switch messages as evidence.
**Warning signs:** `/intimate` produces no switch message (already in intimate mode from a prior test).

### Pitfall 6: Deferred E2E Verification from Phase 9
**What goes wrong:** Phase 9 explicitly deferred browser/inbox E2E verification to Phase 13 (see STATE.md: "Phase 9 browser/inbox E2E verification... delegated to Phase 13 smoke test"). If Phase 13 plans don't explicitly cover EMAI-02/03/04 and AUTH-01 Google OAuth, these requirements will never be verified before milestone declaration.
**How to avoid:** The runbook MUST include: (a) New user signup via Google OAuth → welcome email arrives in inbox, (b) successful Stripe checkout → receipt email arrives, (c) cancellation → cancellation email arrives. These are not optional smoke checks.

### Pitfall 7: admin require_admin Role Mismatch
**What goes wrong:** Testing ADMN-03 (non-admin gets 403) fails because `require_admin` checks `app_metadata.role == "super-admin"` but the admin user was set up with `role = "admin"` (without "super-" prefix).
**Why it happens:** STATE.md decision: `require_admin reads user_metadata.is_admin` was the original plan but the actual implementation in `admin.py` reads `app_metadata.role == "super-admin"`. There was an intermediate decision (`[Phase 12-admin-dashboard]: require_admin reads user_metadata.is_admin`), but the code uses `"super-admin"`.
**How to avoid:** Before admin smoke test, verify operator's Supabase metadata via Dashboard: `raw_app_meta_data` must contain `"role": "super-admin"` (with hyphen, not underscore). Check the actual code in `admin.py` line 39: `(user.app_metadata or {}).get("role") == "super-admin"`.
**Warning signs:** Admin user gets 403 when hitting `/admin/metrics`.

---

## Code Examples

### Automated Paywall Test (SC-5)
```python
# Source: backend/app/dependencies.py require_active_subscription pattern
# Run: cd backend && python -m pytest tests/test_smoke_paywall.py -x -v
import pytest
import httpx

PROD_BASE = "https://avasecret.org"

@pytest.mark.asyncio
async def test_unauthed_chat_returns_401():
    """No credentials -> 401."""
    async with httpx.AsyncClient(base_url=PROD_BASE) as client:
        r = await client.post("/chat", json={"text": "hello"})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"

@pytest.mark.asyncio
async def test_unsubscribed_chat_returns_402(unsubscribed_jwt):
    """Active Supabase user, no subscription row -> 402."""
    async with httpx.AsyncClient(
        base_url=PROD_BASE,
        headers={"Authorization": f"Bearer {unsubscribed_jwt}"},
        timeout=10.0,
    ) as client:
        r = await client.post("/chat", json={"text": "hello"})
    assert r.status_code == 402, f"Expected 402, got {r.status_code}: {r.text}"
    data = r.json()
    assert "Subscription required" in data.get("detail", "")
```

### Usage Events Verification (ADMN-02)
```python
# Source: backend/app/routers/admin.py _count_events pattern
# Confirms all 4 required event types have at least one row
import pytest
from app.database import supabase_admin

REQUIRED_EVENT_TYPES = ["message_sent", "photo_generated", "mode_switch", "subscription_created"]

def test_all_required_event_types_present():
    for event_type in REQUIRED_EVENT_TYPES:
        result = (
            supabase_admin.from_("usage_events")
            .select("id", count="exact")
            .eq("event_type", event_type)
            .execute()
        )
        assert result.count and result.count > 0, \
            f"No usage_events rows found for event_type='{event_type}'"
```

### Health Check Before Smoke Run
```bash
# Confirm production server is live before starting any scenario
curl -sf https://avasecret.org/health && echo "PASS: server alive" || echo "FAIL: server unreachable"
# Expected output: {"status":"ok"}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual ad-hoc testing per phase | Structured milestone gate with recorded evidence | Phase 13 definition | Clear pass/fail criteria; evidence committed to repo |
| Phase 9 deferred browser E2E | Phase 13 runbook covers AUTH-01 and EMAI-02/03/04 | STATE.md decision during Phase 9 | Phase 13 must explicitly include Google OAuth and email inbox checks |
| require_active_subscription with dev bypass | Same code, but production must have STRIPE_SECRET_KEY set | Phase 7 implementation | Pre-flight check for SC-5 mandatory |

**Key architecture fact:** BullMQ is the photo job queue. The `queue.py` enqueues `generate_photo` jobs; `worker_main.py` runs the worker as a separate process. The worker is a separate Docker container. SC-4 smoke test must confirm both containers are running.

---

## Open Questions

1. **Is Stripe in test-mode or live-mode on production?**
   - What we know: `stripe_price_id_basic = price_1T7Y6yGzFiJv4RfGhYAwGZM7` is a live-mode price ID (from STATE.md Phase 8 decision). STRIPE_SECRET_KEY may be a test or live key.
   - What's unclear: Whether SC-5 requires an actual subscribed user (real card charge) or a Stripe test-mode user.
   - Recommendation: Runbook should instruct tester to use an existing subscribed user (operator's own account) for the subscribed-user scenarios (SC-2, SC-3, SC-4, SC-6) and a separate account with no subscription row for SC-5.

2. **Has the operator's account been set up with `app_metadata.role = "super-admin"` in production Supabase?**
   - What we know: Phase 12 wired the admin dashboard and require_admin dependency.
   - What's unclear: Whether the operator has actually set their own admin flag in production Supabase.
   - Recommendation: Add a prerequisite check to the runbook — operator must verify `raw_app_meta_data` in Supabase Dashboard before the admin scenario.

3. **Are there any deferred Google Calendar tokens in production Supabase?**
   - What we know: Calendar OAuth flow requires `google_calendar_tokens` row.
   - What's unclear: Whether the test user has completed the OAuth flow on production.
   - Recommendation: SC-6a prerequisite — confirm or re-authorize Google Calendar before running the skills scenario.

---

## Validation Architecture

> Note: `workflow.nyquist_validation` key is absent from `.planning/config.json` — treating as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x + pytest-asyncio 0.21.x |
| Config file | none (runs from `backend/` directory with `python -m pytest`) |
| Quick run command | `cd backend && python -m pytest tests/test_smoke_paywall.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01/02/03/04 | Production server alive, HTTPS, credentials wired | smoke (manual) | `curl -sf https://avasecret.org/health` | n/a — manual |
| EMAI-01/02/03/04 | Email DNS correct, emails land in inbox | manual-only | n/a | n/a |
| AUTH-01 | Google OAuth sign-in works | manual-only | n/a — requires browser | n/a |
| AUTH-02 | Forgot password email arrives | manual-only | n/a — requires inbox | n/a |
| LAND-01/02/03 | Landing page renders, CTA routes, no prohibited copy | manual-only | n/a — requires browser | n/a |
| SUBS-01/02/03/04/05 | Billing page, portal redirect, cancel flow | manual-only | n/a — requires browser + Stripe | n/a |
| ADMN-01 | Admin metrics endpoint returns data | smoke | `cd backend && python -m pytest tests/test_smoke_admin.py -x` | ❌ Wave 0 |
| ADMN-02 | usage_events has all 4 event types | unit-style | `cd backend && python -m pytest tests/test_smoke_usage_events.py -x` | ❌ Wave 0 |
| ADMN-03 | Non-admin gets 403 from /admin/metrics | automated | `cd backend && python -m pytest tests/test_smoke_paywall.py::test_non_admin_gets_403 -x` | ❌ Wave 0 |
| SC-5 (paywall) | Unsubscribed user POST /chat returns 402 | automated | `cd backend && python -m pytest tests/test_smoke_paywall.py -x` | ❌ Wave 0 |
| SC-1 | reference_image_url non-null within 5 min | manual-only | n/a — async, requires ComfyUI + real avatar | n/a |
| SC-2 | Secretary chat reply received | manual-only | n/a — requires production OpenAI key | n/a |
| SC-3 | Mode switch /intimate /secretary | manual-only | n/a — session state requires live user | n/a |
| SC-4 | BullMQ photo in chat within 5 min | manual-only | n/a — multi-hop async pipeline | n/a |
| SC-6a/6b | Calendar event + web search work | manual-only | n/a — requires Google OAuth + Tavily API | n/a |

**Note on manual-only justification:** SC-1, SC-2, SC-3, SC-4, and SC-6 cannot be automated without a full Playwright/Selenium suite against a production environment with real credentials — an infrastructure investment not justified for a one-time milestone gate. The automated tests cover the paywall contract (SC-5) and database state (ADMN-02) which have deterministic, credential-light verification paths.

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_smoke_paywall.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green + human runbook ALL criteria marked PASS

### Wave 0 Gaps
- [ ] `backend/tests/test_smoke_paywall.py` — covers SC-5 (paywall 402), ADMN-03 (403 non-admin)
- [ ] `backend/tests/test_smoke_usage_events.py` — covers ADMN-02 (usage_events event types)
- [ ] `backend/tests/conftest.py` update — add `unsubscribed_jwt` fixture (production JWT from env var)

*(All other criteria are manual-only as justified above)*

---

## Sources

### Primary (HIGH confidence)
- `backend/app/dependencies.py` — `require_active_subscription` implementation; paywall bypass condition
- `backend/app/routers/admin.py` — `require_admin` implementation (`app_metadata.role == "super-admin"`)
- `backend/app/routers/avatars.py` — `_generate_reference_image_task` 5-step background pipeline
- `backend/app/routers/web_chat.py` — POST /chat dependency chain
- `backend/app/services/jobs/processor.py` — BullMQ photo job pipeline documentation
- `backend/app/services/skills/calendar_skill.py` — NOT_CONNECTED_MSG; OAuth prerequisite
- `.planning/STATE.md` — Phase 9 deferred E2E delegation to Phase 13 (explicit note)

### Secondary (MEDIUM confidence)
- `backend/requirements.txt` — confirms pytest + httpx available (no new deps needed)
- `.planning/REQUIREMENTS.md` — traceability table; all 21 v1.1 requirements mapped to phases 8–12

### Tertiary (LOW confidence)
- None — all findings are grounded in the project codebase directly.

---

## Metadata

**Confidence breakdown:**
- Success criteria coverage: HIGH — all 6 SCs traced to codebase evidence
- Test automation scope: HIGH — correctly constrained to what is automatable without Playwright
- Pitfall identification: HIGH — sourced from STATE.md decisions and implementation code
- Admin role check detail: HIGH — code inspected directly (super-admin vs admin distinction documented)

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable domain — smoke testing patterns change only with major architectural changes)
