---
status: resolved
trigger: "Generated avatar images (reference images and intimate photos) are only accessible for ~24h and then become permanently inaccessible. They should be stored permanently."
created: 2026-03-05T00:00:00Z
updated: 2026-03-05T00:05:00Z
---

## Current Focus

hypothesis: RESOLVED
test: N/A
expecting: N/A
next_action: Archive

## Symptoms

expected: Avatar reference images and generated intimate photos stored in Supabase Storage should be accessible permanently (no expiry). The URLs written to the database should be long-lived or public.
actual: Images only work for 24h then become inaccessible — because signed URLs with 86400s TTL are being stored in the database instead of permanent storage paths.
errors: Unknown — likely silent (images just stop loading after expiry)
reproduction: Generate an avatar reference image or intimate mode photo, wait 24h, try to load the image.
started: Newly discovered design flaw — never worked correctly for long-term.

## Eliminated

- hypothesis: ComfyUI Cloud CDN URLs are stored directly in DB (images expire on ComfyUI side)
  evidence: ComfyUI provider downloads image bytes and returns them as image_bytes; the URL field is set to "". Bytes are then uploaded to Supabase Storage. ComfyUI CDN is not involved in persistence.
  timestamp: 2026-03-05T00:01:00Z

- hypothesis: The bucket is public so public URLs would work without signing
  evidence: Bucket is explicitly created with `options={"public": False}` in both main.py startup and the avatars.py background task. Public URLs will not work.
  timestamp: 2026-03-05T00:01:00Z

## Evidence

- timestamp: 2026-03-05T00:01:00Z
  checked: backend/app/routers/avatars.py lines 95-114 (original)
  found: Step 5 called `create_signed_url(storage_path, 86400)` (24h TTL), then Step 6 wrote that signed URL directly into `avatars.reference_image_url` column in the DB.
  implication: Every reference_image_url stored in the avatars table expired 24 hours after generation.

- timestamp: 2026-03-05T00:01:00Z
  checked: backend/app/services/jobs/processor.py (original)
  found: SIGNED_URL_EXPIRY = 86400. After upload, `create_signed_url(storage_path, SIGNED_URL_EXPIRY)` was called and the signed URL was baked into message content as `[PHOTO]{signed_url}[/PHOTO]`.
  implication: Intimate mode photo messages stored in the messages table contained hardcoded 24h signed URLs.

- timestamp: 2026-03-05T00:01:00Z
  checked: processor.py lines 103-109 (reference image re-signing for i2i)
  found: A 1-hour signed URL is created for the reference image when passing it to ComfyUI as reference_image_url. This is intentional — ComfyUI needs a URL during generation only. NOT a bug.
  implication: This pattern is correct and was left unchanged.

- timestamp: 2026-03-05T00:01:00Z
  checked: main.py and avatars.py bucket creation
  found: The 'photos' bucket is always created with `public: False`. Public URLs not viable.
  implication: All access must be via signed URLs. Fix must be: store paths, re-sign on demand.

## Resolution

root_cause: |
  Two code paths stored 24-hour Supabase signed URLs in database columns instead of permanent storage paths:
  1. avatars.py _generate_reference_image_task: stored signed URL in avatars.reference_image_url (expired 24h after avatar creation).
  2. processor.py process_photo_job: stored signed URL baked into message content as [PHOTO]{url}[/PHOTO] (expired 24h after photo generation).
  The 'photos' Supabase Storage bucket is private (public: False), so public URLs are not usable. The correct pattern is to store the raw storage path and generate fresh signed URLs on demand at read time.

fix: |
  THREE-FILE FIX (path-first, re-sign-at-read-time pattern):

  1. backend/app/routers/avatars.py (_generate_reference_image_task):
     - REMOVED: create_signed_url step (was Step 5)
     - CHANGED: stores raw storage path "{user_id}/reference.jpg" in reference_image_url instead of signed URL
     - ADDED: in GET /avatars/me, if reference_image_url does not start with "http", generate a fresh 1-hour signed URL before returning

  2. backend/app/services/jobs/processor.py:
     - REMOVED: SIGNED_URL_EXPIRY constant and create_signed_url call after upload
     - CHANGED: _deliver_web() stores "[PHOTO_PATH]{storage_path}[/PHOTO_PATH]" in message content instead of a pre-signed URL
     - CHANGED: _deliver_whatsapp() generates a fresh 1-hour signed URL from the storage path at delivery time (not stored anywhere)

  3. backend/app/routers/web_chat.py:
     - ADDED: _rewrite_photo_paths() function: scans messages for [PHOTO_PATH] tokens and replaces them with fresh [PHOTO]{signed_url}[/PHOTO] at read time
     - CHANGED: GET /chat/history calls _rewrite_photo_paths() before returning messages

verification: |
  Code review verification:
  - avatars.py: reference_image_url DB column now stores "{user_id}/reference.jpg" (permanent path). GET /avatars/me re-signs on each call. Frontend polling still works (non-null path value terminates polling).
  - processor.py: messages table content now stores [PHOTO_PATH]{path}[/PHOTO_PATH] (permanent). WhatsApp delivery re-signs at send time. Storage path persists forever in Supabase Storage.
  - web_chat.py: GET /chat/history rewrites [PHOTO_PATH] to fresh [PHOTO]{url}[/PHOTO] before returning. Photos permanently accessible regardless of age.
  - The 1-hour re-signing for i2i reference image in processor.py (Step 2) was correctly identified as intentional and left unchanged.

files_changed:
  - backend/app/routers/avatars.py
  - backend/app/services/jobs/processor.py
  - backend/app/routers/web_chat.py
