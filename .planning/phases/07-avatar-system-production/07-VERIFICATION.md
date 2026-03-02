---
phase: 07-avatar-system-production
verified: 2026-03-02T11:00:00Z
status: human_needed
score: 9/9 truths verified (code-level)
re_verification:
  previous_status: human_needed
  previous_score: 9/9
  gaps_closed:
    - "GAP-3: POST /avatars/me/reference-image now returns 202 immediately via BackgroundTasks — Nginx proxy_read_timeout (60s) can no longer kill the connection"
    - "Frontend polls GET /avatars/me every 3s via pollForReferenceImage(); spinner shown while generating; image displayed when reference_image_url is non-null"
    - "reference_image_url cleared to None before queuing task — prevents stale URL from short-circuiting the new poll"
    - "stopPollingRef prevents concurrent polling loops on Regenerate"
    - "5-minute timeout shows 'Generation timed out — please try again' to the user"
    - "GAP-4: reference_image_url TEXT column added to migration 004 (IF NOT EXISTS) and to AvatarResponse model — PGRST204 crash on POST /avatars/me/reference-image eliminated"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Navigate to /avatar-setup, fill in form, click submit — spinner appears within ~2 seconds; within ~90 seconds a reference image appears showing the avatar from head to toe on a neutral background"
    expected: "Full-body standing image (not face/shoulder crop) displayed on screen. Regenerate button produces a different full-body image. 'Looks perfect' navigates to /chat without redirect loop."
    why_human: "ComfyUI Cloud is an external service requiring live COMFYUI_API_KEY credentials and a running workflow. The 202 fire-and-forget + 3s polling pattern is verified structurally but end-to-end delivery depends on the external service."
  - test: "After seeing the reference image, inspect it visually to confirm full-body framing"
    expected: "Avatar visible from head to toe — full body composition, not portrait or face crop."
    why_human: "Image composition quality (full body vs face crop) cannot be verified by static analysis."
  - test: "With STRIPE_SECRET_KEY and STRIPE_PRICE_ID configured, click Subscribe on /subscribe, complete Stripe test checkout, return to /chat"
    expected: "User can send messages (subscription active). Paywall banner no longer shown."
    why_human: "Requires live Stripe test mode credentials and webhook delivery confirmation."
  - test: "npm run build in frontend, then docker compose up -d from project root. docker compose ps — all 4 services running. curl http://localhost/health returns 200."
    expected: "All services start within 30 seconds. nginx serves React app. /health endpoint responds."
    why_human: "Requires Docker installed and container networking — cannot simulate in static analysis."
---

# Phase 7: Avatar System & Production — Verification Report

**Phase Goal:** Users can customize avatars, receive AI-generated photos, and system is production-ready with billing
**Verified:** 2026-03-02
**Status:** human_needed (all automated checks pass — items require live environment testing)
**Re-verification:** Yes — after gap closure via plans 07-07 (GAP-2), 07-08 (GAP-1), and 07-09 (GAP-3)

---

## Re-Verification Summary

Previous status: `human_needed` (9/9 code-verified) after plans 07-07 and 07-08 closed GAP-2 and GAP-1.

**GAP-3 (RESOLVED by plan 07-09, commits `a6c2856` and `c4d744b`):**

The reference image endpoint previously blocked the HTTP connection for 60–120 seconds waiting for ComfyUI to finish. Nginx's `proxy_read_timeout` (60 seconds) silently killed the connection before the image was ready — the frontend never received the URL and stayed on the form indefinitely.

Resolution:
- `backend/app/routers/avatars.py` (commit `a6c2856`): `generate_reference_image` now accepts `BackgroundTasks`, returns `202 {"status": "generating"}` immediately. A new `_generate_reference_image_task(user_id)` async function runs the full pipeline (ComfyUI generate → watermark → upload → sign URL → write `reference_image_url` to DB) as a FastAPI BackgroundTask. `reference_image_url` is explicitly cleared to `None` before queuing to prevent stale URL from short-circuiting the new poll.
- `frontend/src/api/avatars.ts` (commit `c4d744b`): `generateReferenceImage` renamed to `triggerReferenceImage` (void return, fire-and-forget). New `pollForReferenceImage()` function uses `setInterval` at 3-second intervals; stops and calls `onFound(url)` when `reference_image_url` is non-null; calls `onTimeout()` after 5 minutes (300,000 ms); returns a cleanup function.
- `frontend/src/pages/AvatarSetupPage.tsx` (commit `c4d744b`): `stopPollingRef` (useRef) stores the cleanup function to cancel active polling before Regenerate starts a new poll. Spinner with "Generating your Ava..." shown while `generating=true`. Timeout sets error state "Generation timed out — please try again". `handleApprove` cancels any active poll before navigating.

**GAP-1 and GAP-2 fixes verified as not regressed:**
- `prompt_builder.py` line 48: `"full body, standing, full-length portrait, head to toe,"` still present; no "portrait" prefix.
- `comfyui_provider.py`: `history_data.get(prompt_id, {})` unwrap still present; `history_data["outputs"]` at root not present.

No regressions detected in any previously-passing truth.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | DB migration adds gender/nationality columns to avatars table and creates subscriptions table with RLS | VERIFIED | `backend/migrations/004_phase7_avatar_fields.sql` — ALTER TABLE adds gender/nationality (IF NOT EXISTS); CREATE TABLE subscriptions with CHECK constraint, UNIQUE(user_id), RLS enabled, select policy present |
| 2 | AvatarCreate and AvatarResponse include gender, nationality, age fields with 20+ enforcement | VERIFIED | `backend/app/models/avatar.py` — AvatarCreate.age Field(ge=20); gender Optional[str] max_length=50; nationality Optional[str] max_length=100; AvatarResponse mirrors same fields |
| 3 | After login with no avatar, user is redirected to /avatar-setup; form collects all AVTR fields | VERIFIED | `frontend/src/App.tsx` — OnboardingGate uses useQuery(['avatar']) -> getMyAvatar(); avatar===null triggers Navigate to /avatar-setup. AvatarSetupPage.tsx has form fields: name, age (min=20), gender, nationality, physical_description, personality picker |
| 4 | ImageProvider Protocol exists and ReplicateProvider satisfies it (ARCH-03) | VERIFIED | `backend/app/services/image/base.py` — @runtime_checkable ImageProvider Protocol with async generate(). ReplicateProvider and ComfyUIProvider both implement generate() with matching signature. GeneratedImage extended with image_bytes field |
| 5 | prompt_builder.build_avatar_prompt() generates full-body framing for avatar images | VERIFIED | `backend/app/services/image/prompt_builder.py` line 48: `parts.append("full body, standing, full-length portrait, head to toe,")`. Prefix is "Professional photograph" (no portrait bias). `backend/app/routers/avatars.py` line 41: background task passes "neutral background, natural light, full body visible, standing". Commits 93fc6a5 and a6c2856. |
| 6 | POST /avatars/me/reference-image returns 202 immediately — frontend polls GET /avatars/me every 3s until reference_image_url appears | VERIFIED | `backend/app/routers/avatars.py` line 165: `status_code=202` on decorator; line 192: `background_tasks.add_task(_generate_reference_image_task, user_id)`; line 194: returns `{"status": "generating"}`. `frontend/src/api/avatars.ts`: `triggerReferenceImage()` void POST; `pollForReferenceImage()` setInterval 3s, 300_000ms timeout, cleanup returned. `frontend/src/pages/AvatarSetupPage.tsx`: `stopPollingRef` stores cleanup; spinner while `generating=true`. Commits a6c2856 and c4d744b. Live delivery requires human test. |
| 7 | Stripe billing gate: POST /billing/checkout returns checkout_url; POST /chat returns 402 without active subscription | VERIFIED | `backend/app/routers/billing.py` — /billing/checkout reads settings.stripe_price_id; /billing/webhook handles checkout.session.completed, invoice.payment_failed, customer.subscription.deleted. `backend/app/dependencies.py` — require_active_subscription raises HTTP 402. `backend/app/routers/web_chat.py` — POST /chat uses Depends(require_active_subscription) |
| 8 | Docker Compose starts nginx + backend + worker + redis with a single command | VERIFIED | `docker-compose.yml` — 4 services: nginx (nginx:alpine), backend (uvicorn), worker (python worker_main.py), redis (redis:7-alpine with AOF persistence). `nginx.conf` — proxy_pass to backend:8000, SPA fallback |
| 9 | System ready for beta: Sentry initialized, .env.example documents all env vars, worker_main.py is a standalone entry point | VERIFIED | `backend/app/main.py` — sentry_sdk.init() called before FastAPI(). `backend/.env.example` — documents STRIPE_SECRET_KEY, STRIPE_PRICE_ID, REPLICATE_API_TOKEN, SENTRY_DSN, COMFYUI_API_KEY, REDIS_URL, UptimeRobot setup instructions. `backend/worker_main.py` — standalone asyncio process with concurrency=3, blocks on asyncio.Future() |

**Score: 9/9 truths verified at code level**
Truth 6 additionally requires human testing of the live fire-and-forget + polling flow.
Truths 5 and 6 additionally require human testing of the live ComfyUI workflow for image quality.

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/migrations/004_phase7_avatar_fields.sql` | DB schema for gender/nationality + subscriptions | VERIFIED | 66 lines; gender, nationality, subscriptions with RLS |
| `backend/app/services/image/base.py` | ImageProvider Protocol + GeneratedImage | VERIFIED | @runtime_checkable Protocol; GeneratedImage extended with image_bytes field |
| `backend/app/services/image/replicate_provider.py` | ReplicateProvider concrete implementation | VERIFIED | httpx-based polling implementation; satisfies Protocol |
| `backend/app/services/image/comfyui_provider.py` | ComfyUIProvider (active provider) with correct history_v2 parsing | VERIFIED | 4-step flow; history_data.get(prompt_id) unwrap; per-operation httpx timeouts |
| `backend/app/services/image/prompt_builder.py` | Avatar fields -> FLUX prompt with full-body directive | VERIFIED | full-body directive at line 48; no portrait bias in prefix; all avatar fields assembled |
| `backend/app/services/image/watermark.py` | Pillow watermark + C2PA metadata | VERIFIED | Pillow alpha_composite watermark at bottom-right; returns JPEG bytes |
| `backend/app/models/avatar.py` | AvatarCreate/AvatarResponse with gender, nationality | VERIFIED | Both models include gender/nationality Optional[str] |
| `backend/app/routers/avatars.py` | Avatar CRUD; POST /me/reference-image returns 202 + BackgroundTasks; background task writes reference_image_url to DB | VERIFIED | status_code=202; BackgroundTasks injected; _generate_reference_image_task defined; reference_image_url cleared before queuing; full-body scene_description passed to prompt builder; supabase_admin used in task. Commit a6c2856. |
| `frontend/src/api/avatars.ts` | triggerReferenceImage() fire-and-forget POST; pollForReferenceImage() setInterval polling with 5-min timeout and cleanup | VERIFIED | triggerReferenceImage void return; pollForReferenceImage setInterval 3s / 300_000ms timeout; cleanup function returned; active flag prevents concurrent polls. Commit c4d744b. |
| `frontend/src/pages/AvatarSetupPage.tsx` | Spinner while polling; stopPollingRef cancels poll on Regenerate; timeout error state; approve navigates to /chat | VERIFIED | generating state + spinner; stopPollingRef stores cleanup; timed out error message; handleApprove calls invalidateQueries + navigate. Commit c4d744b. |
| `backend/app/routers/billing.py` | POST /billing/checkout + POST /billing/webhook | VERIFIED | Both routes registered; webhook handles 3 event types; reads settings.stripe_price_id |
| `backend/app/services/billing/subscription.py` | activate_subscription, deactivate_subscription, get_subscription_status | VERIFIED | All 3 functions present; upsert with on_conflict="user_id"; uses supabase_admin |
| `backend/app/dependencies.py` | require_active_subscription raises 402 | VERIFIED | Dependency present; raises HTTP 402 when status != 'active' |
| `backend/app/config.py` | stripe_secret_key, stripe_price_id, sentry_dsn, redis_url, comfyui_api_key fields | VERIFIED | All fields present with empty-string defaults |
| `backend/app/services/jobs/queue.py` | enqueue_photo_job with attempts=3 exponential backoff | VERIFIED | Queue singleton; enqueue_photo_job with attempts=3, backoff exponential 2s |
| `backend/app/services/jobs/processor.py` | Full 8-step pipeline: prompt -> ComfyUI -> watermark -> upload -> sign -> audit -> deliver | VERIFIED (structural) | Full pipeline present; uses ComfyUIProvider; web/WhatsApp delivery split; failure notification on retries exhausted |
| `backend/worker_main.py` | BullMQ Worker entry point, concurrency=3 | VERIFIED | Standalone asyncio; Worker with concurrency=3; asyncio.Future() blocking |
| `frontend/src/App.tsx` | OnboardingGate redirects to /avatar-setup when no avatar | VERIFIED | OnboardingGate component; useQuery(['avatar']); Navigate to /avatar-setup when null |
| `frontend/src/pages/SubscribePage.tsx` | Stripe Checkout redirect with loading state | VERIFIED | createCheckoutSession(); window.location.href redirect; cancel feedback |
| `frontend/src/api/billing.ts` | createCheckoutSession() | VERIFIED | POST /billing/checkout; returns {checkout_url} |
| `docker-compose.yml` | 4 services: nginx + backend + worker + redis | VERIFIED | All 4 services; worker runs python worker_main.py; redis AOF persistence |
| `nginx.conf` | Reverse proxy + SPA fallback | VERIFIED | proxy_pass http://backend:8000; try_files SPA fallback |
| `backend/.env.example` | All env vars documented | VERIFIED | STRIPE_SECRET_KEY, COMFYUI_API_KEY, SENTRY_DSN, REDIS_URL, UptimeRobot instructions |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/routers/avatars.py` | `_generate_reference_image_task` | `background_tasks.add_task(_generate_reference_image_task, str(user.id))` | WIRED | Line 192 confirmed. 202 returned on line 194. Commit a6c2856. |
| `backend/app/routers/avatars.py` | `supabase_admin (avatars table)` | `supabase_admin.from_("avatars").update({"reference_image_url": signed_url}).eq("user_id", user_id)` in background task | WIRED | Lines 78–80 confirmed. supabase_admin service role used (no user JWT in background context). |
| `frontend/src/api/avatars.ts` | `POST /avatars/me/reference-image` | `triggerReferenceImage()` — expects 202, does NOT wait for image URL in response | WIRED | Lines 59–69 confirmed. Function returns void. |
| `frontend/src/api/avatars.ts` | `GET /avatars/me` | `pollForReferenceImage()` — setInterval every 3s, stops when avatar.reference_image_url is non-null | WIRED | Lines 85–127 confirmed. Uses getMyAvatar(); checks avatar?.reference_image_url. |
| `frontend/src/pages/AvatarSetupPage.tsx` | `frontend/src/api/avatars.ts` | `triggerReferenceImage(token)` + `pollForReferenceImage(token, onFound, onTimeout, onError)` | WIRED | Lines 91 and 99 confirmed. stopPollingRef stores cleanup function. |
| `frontend/src/pages/AvatarSetupPage.tsx` | Active poll cancellation | `stopPollingRef.current()` called at start of handleGenerateReference (Regenerate path) and in handleApprove | WIRED | Lines 79–81 and 124–127 confirmed. Prevents concurrent polling loops. |
| `backend/app/services/image/comfyui_provider.py` | ComfyUI Cloud /api/history_v2/{prompt_id} | `_fetch_history_and_download` unwraps `history_data.get(prompt_id, {})` before reading outputs | WIRED | Confirmed present; no regression from commit ce1834c. |
| `backend/app/routers/avatars.py (_generate_reference_image_task)` | `backend/app/services/image/prompt_builder.py` | `build_avatar_prompt(avatar, "neutral background, natural light, full body visible, standing")` | WIRED | Lines 39–42 confirmed. Full-body scene_description in background task. |
| `backend/app/services/image/prompt_builder.py` | ComfyUI full-body directive | `"full body, standing, full-length portrait, head to toe,"` appended before quality anchors | WIRED | Line 48 confirmed; no regression. |
| `backend/app/services/chat.py` | `backend/app/services/jobs/queue.py` | `enqueue_photo_job()` in intimate mode tool_calls detection | WIRED | SEND_PHOTO_TOOL defined; finish_reason=="tool_calls" branch calls enqueue_photo_job() |
| `backend/app/routers/web_chat.py` | `backend/app/dependencies.py` | `require_active_subscription` on POST /chat | WIRED | Depends(require_active_subscription) in send_message signature |
| `backend/app/routers/billing.py` | `backend/app/config.py` | `settings.stripe_price_id` (BILL-02 config-driven) | WIRED | if not settings.stripe_price_id: raises 503; price passed to create_checkout_session |
| `backend/app/routers/billing.py` | `backend/app/services/billing/subscription.py` | `activate_subscription()` / `deactivate_subscription()` in webhook | WIRED | Both called from stripe_webhook handler |
| `frontend/src/App.tsx` | `GET /avatars/me` | OnboardingGate useQuery — redirects to /avatar-setup when null | WIRED | queryFn: getMyAvatar(token); avatar===null triggers Navigate |
| `frontend/src/pages/SubscribePage.tsx` | `POST /billing/checkout` | `createCheckoutSession()` + window.location.href redirect | WIRED | handleSubscribe calls createCheckoutSession(token), then window.location.href = checkout_url |
| `frontend/src/pages/ChatPage.tsx` | `POST /chat (402 response)` | subscriptionRequired state + banner with /subscribe link | WIRED | err.status===402 sets subscriptionRequired=true; banner rendered with href="/subscribe" |
| `backend/app/services/jobs/processor.py` | `backend/app/services/image/comfyui_provider.py` | `ComfyUIProvider().generate()` called with prompt + reference_image_url | WIRED | _image_provider = ComfyUIProvider(); called in process_photo_job |
| `backend/app/services/jobs/processor.py` | `supabase_admin.storage` | upload watermarked JPEG to photos bucket | WIRED | supabase_admin.storage.from_(PHOTO_BUCKET).upload(...) in Step 6 |
| `backend/app/main.py` | `sentry_sdk` | `sentry_sdk.init(dsn=settings.sentry_dsn)` before FastAPI() | WIRED | sentry_sdk.init() at module top before app = FastAPI() |
| `docker-compose.yml` | `backend/worker_main.py` | worker service command: python worker_main.py | WIRED | command: python worker_main.py in worker service |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| AVTR-01 | 07-02, 07-04 | User can select avatar gender | VERIFIED | AvatarCreate.gender field; form input in AvatarSetupPage; insert in create_avatar |
| AVTR-02 | 07-02, 07-04 | User can select avatar age (20+ enforced, hard floor) | VERIFIED | AvatarCreate.age Field(ge=20); form min={20} in AvatarSetupPage |
| AVTR-03 | 07-02, 07-04 | User can select avatar nationality/race | VERIFIED | AvatarCreate.nationality field; form input in AvatarSetupPage; insert in create_avatar |
| AVTR-04 | 07-02, 07-04 | User can describe avatar appearance in free text | VERIFIED | AvatarCreate.physical_description Optional[str] max_length=2000; textarea in AvatarSetupPage |
| AVTR-05 | 07-01, 07-04, 07-07, 07-08, 07-09 | Avatar definition feeds into image generation for consistent character photos | VERIFIED (code) | build_avatar_prompt() wired in background task and processor.py. Full-body directive present (GAP-1 closed). history_v2 correctly parsed (GAP-2 closed). 202 fire-and-forget + polling prevents Nginx timeout (GAP-3 closed). Human test required to confirm end-to-end delivery with live ComfyUI. |
| INTM-03 | 07-03, 07-04, 07-07, 07-09 | Bot sends AI-generated photos during intimate conversations | VERIFIED (code) | SEND_PHOTO_TOOL wired in chat.py; enqueue_photo_job() called; processor pipeline present; ComfyUIProvider delivery fix applied (GAP-2 closed). Human test required for live delivery. |
| ARCH-03 | 07-01 | Modular image generation — provider swappable without changing photo flow | VERIFIED | @runtime_checkable ImageProvider Protocol; ReplicateProvider and ComfyUIProvider both satisfy Protocol via structural typing; processor.py uses _image_provider without referencing concrete class directly |
| BILL-01 | 07-02, 07-05 | Flexible billing infrastructure supporting multiple pricing models | VERIFIED | Stripe Checkout + webhook; subscriptions table; activate/deactivate helpers; config-driven price_id |
| BILL-02 | 07-02, 07-05 | Billing model customizable without code changes (config-driven) | VERIFIED | stripe_price_id read from settings (env); no hardcoded amounts anywhere in billing code |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | No blockers or warnings. All previously-flagged issues resolved. |

Previously-flagged blockers and their resolution:
- `prompt_builder.py`: No full-body directive — RESOLVED (commit 93fc6a5)
- `avatars.py` line 107: "full face" scene_description — RESOLVED (commit 93fc6a5; background task at line 41 now passes full-body scene)
- `comfyui_provider.py`: wrong root key in history_v2 response — RESOLVED (commit ce1834c)
- `processor.py`: stale "Call Replicate API" docstring — RESOLVED (commit 93fc6a5)
- `avatars.py`: blocking HTTP connection for 60–120s — RESOLVED (commits a6c2856 and c4d744b; GAP-3)

---

## Human Verification Required

All code-level gaps are closed. The following items require testing in a live environment with real credentials.

### 1. Avatar Onboarding End-to-End (fire-and-forget + polling)

**Test:** Start backend with valid `COMFYUI_API_KEY`. Navigate to `/avatar-setup`, fill in name, age (20+), gender, nationality, physical description, and personality. Click "Create Ava & Generate Photo".
**Expected:**
- The form disappears and "Generating your Ava..." spinner appears within ~2 seconds (POST returns 202 immediately — no 60-second wait).
- After 60–90 seconds the spinner disappears and a reference image appears on the page, showing the avatar from head to toe on a neutral background (not a face/shoulder crop).
- Backend logs show "Background task: reference image ready for user {id}" confirming the full pipeline completed.
- Clicking Regenerate shows the spinner again and produces a visually different full-body image after another 60–90 seconds.
- Clicking "Looks perfect" navigates to `/chat` without redirect loop.
**Why human:** ComfyUI Cloud requires live `COMFYUI_API_KEY` credentials and a running workflow. The 202 fire-and-forget pattern and 3s polling loop are verified structurally but end-to-end delivery depends on the external service.

### 2. Full-Body Image Composition Quality

**Test:** After the reference image appears in the onboarding flow above, inspect it visually.
**Expected:** Avatar visible from head to toe — full body composition, not portrait or face crop.
**Why human:** Image composition quality cannot be verified by static analysis.

### 3. Stripe Checkout Flow

**Test:** With `STRIPE_SECRET_KEY` and `STRIPE_PRICE_ID` configured in Stripe test mode, navigate to `/subscribe` and click Subscribe. Complete the Stripe test checkout. Return to `/chat`.
**Expected:** User can send messages without the 402 paywall banner. `/billing/webhook` receives `checkout.session.completed` and activates the subscription row in Supabase.
**Why human:** Requires live Stripe test mode credentials and webhook delivery confirmation.

### 4. Docker Compose Production Smoke Test

**Test:** Run `npm run build` in `frontend/`, then `docker compose up -d` from project root. Run `docker compose ps` — all 4 services should show as running. Run `curl http://localhost/health`.
**Expected:** All 4 services (nginx, backend, worker, redis) start within 30 seconds. nginx serves the React SPA. `/health` returns 200.
**Why human:** Requires Docker installed and container networking — cannot simulate in static analysis.

---

## Gaps Summary

No code-level gaps remain. All three blocking bugs are fully resolved:

**GAP-2 (RESOLVED, commit ce1834c):** `_fetch_history_and_download` correctly reads `history_data.get(prompt_id, {})["outputs"]`. The ComfyUI Cloud API wraps the generation result under the `prompt_id` key — the old code always returned `{}`, causing HTTP 500.

**GAP-1 (RESOLVED, commit 93fc6a5):** `build_avatar_prompt()` appends `"full body, standing, full-length portrait, head to toe,"` before quality anchors. Prefix changed to "Professional photograph". `generate_reference_image()` background task now passes `"neutral background, natural light, full body visible, standing"` as scene_description.

**GAP-3 (RESOLVED, commits a6c2856 and c4d744b):** `POST /avatars/me/reference-image` returns 202 immediately via FastAPI BackgroundTasks. `reference_image_url` is cleared to `None` before queuing to ensure polling waits for the new image. Frontend `pollForReferenceImage()` polls GET /avatars/me every 3 seconds with a 5-minute timeout. `stopPollingRef` prevents concurrent polling loops on Regenerate. Nginx `proxy_read_timeout` can no longer kill the connection.

**GAP-4 (RESOLVED, commit from plan 07-10):** `POST /avatars/me/reference-image` crashed with `PGRST204: Could not find the 'reference_image_url' column of 'avatars' in the schema cache`. Root cause: migration 004 never included `reference_image_url TEXT` in the ALTER TABLE block, and `AvatarResponse` in `avatar.py` did not expose the field. Fixed by: (1) adding `ADD COLUMN IF NOT EXISTS reference_image_url TEXT` to `backend/migrations/004_phase7_avatar_fields.sql`; (2) adding `reference_image_url: Optional[str] = None` to `AvatarResponse` in `backend/app/models/avatar.py`; (3) applying the column addition via Supabase Dashboard SQL Editor.

Phase 7 goal is achieved at the code level. Human verification of the live onboarding flow (spinner → image delivery → full-body composition) is the remaining gate before marking the phase fully complete.

---

_Verified: 2026-03-02_
_Verifier: Claude (gsd-verifier)_
_Re-verification after gap-closure plans 07-07 (GAP-2), 07-08 (GAP-1), 07-09 (GAP-3), and 07-10 (GAP-4)_
