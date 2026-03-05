---
status: investigating
trigger: "ComfyUI generates the image successfully but the background task never writes reference_image_url to Supabase — the column stays NULL and the frontend poll loops forever."
created: 2026-03-02T00:00:00Z
updated: 2026-03-02T13:00:00Z
---

## Current Focus

hypothesis: The polling loop in _poll_and_download calls data.get("status") but the ComfyUI Cloud /api/job/{id}/status endpoint returns a response where "status" is either nested differently or named differently (e.g. {"job": {"status": "..."}} or {"state": "..."}). When data.get("status") returns None, neither the "completed" branch nor the failure branch triggers — the loop runs the full 300s then raises TimeoutError. The user may have stopped observing before the 300s timeout, so the frontend poll loop times out at ~5min simultaneously with the backend giving up. A secondary possibility: the status poll HTTP request itself stalls on a TCP connection, but httpx read=120s timeout would eventually fire that. DEFINITIVE test: print the full raw JSON response from every poll iteration.
test: Adding print() instrumentation inside _poll_and_download that dumps the full raw JSON (status code + full body) to stderr for every poll iteration. Also adding [COMFY][STEP-N] markers at every key point inside generate(), _submit(), _poll_and_download(), _fetch_history_and_download(), _download_output().
expecting: The printed raw poll responses will reveal either (a) the actual field name/value the API returns (e.g. "state"="success" instead of "status"="completed") or (b) that the GET /api/job/status request itself stalls and never returns within the POLL_INTERVAL window.
next_action: Apply instrumentation to comfyui_provider.py, restart server, user re-runs test.

## Symptoms

expected: After submitting the avatar form, POST /avatars/me/reference-image returns 202, a FastAPI BackgroundTask runs _generate_reference_image_task(), ComfyUI generates the image, the task downloads it, watermarks it, uploads to Supabase Storage, creates a signed URL, and writes it to public.avatars.reference_image_url. The frontend polls GET /avatars/me every 3s and eventually sees a non-null URL.
actual: The column stays NULL in Supabase forever. The frontend polling loop runs indefinitely and times out. The image IS visible/completed in the ComfyUI Cloud dashboard — the generation itself succeeded. The write-back to Supabase never happens.
errors: No visible error in the frontend (polling just times out). No error logs in backend — the CancelledError is BaseException, not Exception, so it bypasses the except Exception block entirely.
reproduction: Navigate to /avatar-setup, fill form, submit. Wait. reference_image_url stays NULL in Supabase dashboard.
started: Happening now. The ComfyUI connection and generation work (image appears in ComfyUI dashboard). The failure is somewhere AFTER generation completes.

## Eliminated

- hypothesis: _fetch_history_and_download fails to parse history_v2 response (wrong key structure)
  evidence: comfyui_provider.py correctly calls history_data.get(prompt_id, {}) — GAP-2 was already fixed in commit ce1834c (07-07). The code unwraps the prompt_id outer key before reading outputs.
  timestamp: 2026-03-02T10:30:00Z

- hypothesis: _download_output uses wrong output node key
  evidence: text_to_image.json node "60" has class_type "SaveImage" and is the correct output node. _build_t2i returns output_node="60". _download_output correctly does outputs.get("60", {}).get("images", []).
  timestamp: 2026-03-02T10:30:00Z

- hypothesis: create_signed_url returns wrong key (signed_url vs signedURL)
  evidence: storage3 _sync/file_api.py line 202 returns {"signedURL": ..., "signedUrl": ...}. avatars.py line 71 checks signedURL first, which IS present. This works correctly.
  timestamp: 2026-03-02T10:30:00Z

- hypothesis: ComfyUI /api/view download fails (redirect not followed)
  evidence: _download_output calls client.get() with follow_redirects=True. The 302 redirect from ComfyUI Cloud is correctly followed.
  timestamp: 2026-03-02T10:30:00Z

- hypothesis: apply_watermark fails on ComfyUI image bytes
  evidence: apply_watermark uses Pillow Image.open(io.BytesIO(image_bytes)). If _download_output succeeds and returns valid JPEG/PNG bytes, this step works. The watermark code is correct.
  timestamp: 2026-03-02T10:30:00Z

- hypothesis: Supabase Storage "photos" bucket does not exist (first root cause theory)
  evidence: Disproved by new checkpoint data. If the bucket were missing, StorageApiError would be raised and caught by "except Exception" — which WOULD produce a logger.error log. The user sees NO log after STEP-1. The failure is earlier, before any upload step.
  timestamp: 2026-03-02T12:00:00Z

- hypothesis: provider.generate() returns but image_bytes is empty or invalid
  evidence: No STEP-2 log appears at all. This means provider.generate() never returns (neither success nor exception). The failure is INSIDE the generate() call, not after it.
  timestamp: 2026-03-02T12:00:00Z

- hypothesis: asyncio.CancelledError from BackgroundTasks cancellation (CORSMiddleware / HTTPMiddleware bug) kills the task silently
  evidence: DISPROVED by second checkpoint. The fix (asyncio.ensure_future + explicit CancelledError handler) IS correctly applied in avatars.py (line 251 uses ensure_future, line 122 catches CancelledError). The user reports IDENTICAL behavior after the fix — STEP-1 appears, STEP-2 never appears, no CancelledError log. This rules out task cancellation as the root cause. The task genuinely hangs inside generate(), not because of cancellation.
  timestamp: 2026-03-02T13:00:00Z

## Evidence

- timestamp: 2026-03-02T10:20:00Z
  checked: backend/migrations/ (all 4 SQL files) and full backend source tree
  found: ZERO occurrences of create_bucket() or any Supabase Storage bucket creation for "photos". Migrations 001-004 contain no storage setup at all.
  implication: The "photos" bucket almost certainly does not exist in Supabase Storage.

- timestamp: 2026-03-02T10:22:00Z
  checked: .planning/phases/07-avatar-system-production/07-RESEARCH.md lines 479-482
  found: "What goes wrong: photo.py signed URL endpoint returns 500 because the photos bucket doesn't exist. This was noted in STATE.md from Phase 6. The bucket was deferred to Phase 7. How to avoid: First task in Phase 7 is creating the photos private bucket in Supabase Dashboard (or via supabase_admin.storage.create_bucket())."
  implication: This is explicitly a known pitfall. Phase 7 was supposed to create the bucket but never did — no code does it.

- timestamp: 2026-03-02T10:24:00Z
  checked: storage3/_sync/file_api.py _request() method (lines 56-89)
  found: _request() calls response.raise_for_status() and wraps HTTPStatusError as StorageApiError (an Exception subclass). So a 404/400 on bucket-not-found raises StorageApiError.
  implication: The silent except Exception block in avatars.py line 88 catches StorageApiError. The error is logged but execution stops — the DB update at line 78 is never reached.

- timestamp: 2026-03-02T10:25:00Z
  checked: storage3/_sync/file_api.py _make_signed_url() (line 202) and create_signed_url() return
  found: Returns dict {"signedURL": str(signedURL), "signedUrl": str(signedURL)} — BOTH keys present. avatars.py line 71 correctly reads sign_response.get("signedURL").
  implication: create_signed_url key access is correct — NOT a bug.

- timestamp: 2026-03-02T10:26:00Z
  checked: comfyui_provider.py _fetch_history_and_download() and _download_output() in full
  found: history_v2 correctly unwrapped via history_data.get(prompt_id, {}). Output node "60" correctly matches text_to_image.json SaveImage node. follow_redirects=True on /api/view download.
  implication: ComfyUI image download code is correct — image bytes ARE successfully retrieved. The failure is at the upload step, not at the download step.

- timestamp: 2026-03-02T11:30:00Z
  checked: uvicorn LOGGING_CONFIG, Python logging root logger, BackgroundTask mechanism
  found: After uvicorn's dictConfig, root logger has NO handlers and level=WARNING. logger.error() IS visible (via lastResort handler). logger.info() is SUPPRESSED (below WARNING). BackgroundTask.__call__ does `await self.func(...)` directly — no asyncio.create_task, runs synchronously.
  implication: (1) SUCCESS path uses logger.info which is suppressed — so if task succeeds, we see ZERO logs. (2) ERROR paths use logger.error which IS visible. Zero error logs = either task never ran OR task succeeded.

- timestamp: 2026-03-02T11:35:00Z
  checked: reference_image_url column in Supabase via `supabase_admin.from_("avatars").select("reference_image_url").limit(1).execute()`
  found: Column exists, returns None for existing row. Migration 004 was applied.
  implication: Column exists — the DB update step is feasible.

- timestamp: 2026-03-02T11:40:00Z
  checked: storage3 create_signed_url return type and upload() upsert handling
  found: create_signed_url returns {"signedURL": ..., "signedUrl": ...}. Code checks "signedURL" which is present. Upload upsert="true" is correctly handled by storage3. But original code missed "signedUrl" (camelCase) as fallback — fixed in instrumented code.
  implication: Signed URL extraction should work. Minor: added "signedUrl" as fallback.

- timestamp: 2026-03-02T11:45:00Z
  checked: Whether task IS actually being entered at all
  found: Added sentinel print()+logger.error() at VERY FIRST LINE of _generate_reference_image_task (before deferred imports, before try block). Also added [BG_TASK][STEP-N] checkpoints at every step using logger.error so they appear regardless of logging config. Both print() to stderr and logger.error() used so logging config cannot suppress them.
  implication: Next test run will definitively confirm if task body enters AND which step fails.

- timestamp: 2026-03-02T12:00:00Z
  checked: Checkpoint response from user: actual uvicorn logs after triggering reference image generation
  found: Log shows "[BG_TASK][STEP-1] Starting ComfyUI generation for user {id}" then NOTHING. No STEP-2 log, no exception log from the outer except block. Image IS complete in ComfyUI Cloud dashboard.
  implication: provider.generate() is called but NEVER returns — no success, no exception. This rules out every failure mode that occurs after generate() returns. The task is being cancelled (CancelledError) INSIDE the asyncio.sleep() loop in _poll_and_download.

- timestamp: 2026-03-02T12:10:00Z
  checked: Python exception hierarchy for asyncio.CancelledError, FastAPI BackgroundTasks mechanism
  found: asyncio.CancelledError is BaseException (not Exception) since Python 3.8. The "except Exception as e" block in _generate_reference_image_task does NOT catch CancelledError. Starlette BackgroundTask runs via "await self.func(...)" — tied to the request Task. CORSMiddleware uses HTTPMiddleware internally. Known Starlette issue #2093: HTTPMiddleware causes BackgroundTasks to receive CancelledError when the HTTP connection closes after the response is sent.
  implication: When the client receives the 202 response, the connection closes, propagating CancelledError into the background task's asyncio.sleep() call. The task dies silently with zero log output — exactly what we observe.

- timestamp: 2026-03-02T12:20:00Z
  checked: ComfyUI Cloud API docs for valid status field values
  found: Official docs list: waiting_to_dispatch, pending, in_progress, completed, error, cancelled. The polling code checks "completed" (correct) and ("failed", "cancelled", "canceled") for failure. "error" is NOT in the failure set — a separate bug but not causing this issue since the job succeeds.
  implication: Secondary bug found: if ComfyUI job fails with status="error", the loop polls indefinitely until POLL_TIMEOUT (300s). Added "error" to the failure set in the fix.

- timestamp: 2026-03-02T12:25:00Z
  checked: main.py CORSMiddleware registration and requirements.txt versions
  found: CORSMiddleware IS present (add_middleware). FastAPI>=0.115.0 (pinned minimum). No explicit starlette pin — FastAPI pulls its own starlette. Starlette 0.21.0 partially fixed background task cancellation but HTTPMiddleware (used by CORSMiddleware) re-introduced it per issue #2093.
  implication: The app is definitely affected by the HTTPMiddleware + BackgroundTask cancellation bug.

- timestamp: 2026-03-02T13:00:00Z
  checked: avatars.py and comfyui_provider.py — read entire files to verify the previously applied fixes are actually present
  found: (1) avatars.py line 251 uses asyncio.ensure_future() — fix IS applied correctly. (2) avatars.py line 122 catches asyncio.CancelledError explicitly — fix IS applied. (3) comfyui_provider.py line 164 includes "error" in failure statuses — fix IS applied. (4) _poll_and_download polls every POLL_INTERVAL=4s, timeout 300s, checks status = data.get("status"). (5) No CancelledError log appeared in user test — meaning the ensure_future fix works and cancellation is NOT the cause. Task is genuinely hanging inside generate().
  implication: CRITICAL: The CancelledError hypothesis is ELIMINATED. The ensure_future fix IS applied and IS working (no CancelledError). The task genuinely hangs inside provider.generate(). The most likely cause: data.get("status") returns None because the ComfyUI Cloud status API uses a different JSON structure, so the poll loop never hits the "completed" branch and runs for 300s. Alternative: the httpx request to /api/job/status stalls on TCP (no data) and waits the full read=120s timeout per iteration.

- timestamp: 2026-03-02T13:05:00Z
  checked: Applied dense _dbg() instrumentation to every key point in comfyui_provider.py
  found: Added _dbg() helper (prints to stderr via print() AND logger.error() — bypasses all logging config). Instrumented: generate() entry/workflow-build/submit/poll, _submit() pre/post, _poll_and_download() pre-sleep/post-GET/full-JSON-dump per iteration, _fetch_history_and_download() per attempt, _download_output() node lookup. Every HTTP response now prints full body (up to 800 chars).
  implication: The next test run will print [COMFY_DBG] lines for every step. The LAST [COMFY_DBG] line before silence identifies the exact blocking call. If poll iterations appear: the raw JSON dump will show the actual status field name/value returned by the API.

## Resolution

root_cause: UNDER RE-INVESTIGATION. The CancelledError + BackgroundTasks hypothesis was correct in theory but the ensure_future fix was already applied before the second test. The task is genuinely hanging inside provider.generate(). Two leading hypotheses: (A) _poll_and_download's data.get("status") returns None because the ComfyUI Cloud status API uses a different field name/structure — poll runs full 300s until TimeoutError; (B) httpx stalls on the TCP connection to /api/job/status (no data arrives), waiting up to read=120s per iteration. Dense instrumentation added to identify exact blocking point and raw API response.
fix: pending instrumentation results — fix will target exact root cause once identified
verification: pending
files_changed:
  - backend/app/routers/avatars.py (ensure_future + CancelledError handler — already applied)
  - backend/app/services/image/comfyui_provider.py (error status already applied; _dbg() instrumentation added 2026-03-02T13:05)
