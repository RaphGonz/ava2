import asyncio
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_authed_supabase
from app.models.avatar import AvatarCreate, AvatarResponse, PersonaUpdateRequest
from app.services.session.store import get_session_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/avatars", tags=["avatars"])


async def _generate_reference_image_task(user_id: str) -> None:
    """
    Background task: generate -> watermark -> upload -> write reference_image_url to avatar DB row.

    Uses supabase_admin (service role) for all DB and Storage operations -- no user JWT available
    in background task context (established pattern: see Phase 2 decision in STATE.md).

    Failures are logged but NOT re-raised -- the background task must not crash the worker.
    The frontend polling loop will time out with a user-facing error message after 5 minutes.
    """
    # Sentinel log: very first line of function -- confirms task body is executing.
    # Uses print() in addition to logger to bypass any logging configuration issues.
    import sys
    print(f"[BG_TASK] _generate_reference_image_task ENTERED for user {user_id}", flush=True, file=sys.stderr)
    logger.error(f"[BG_TASK] _generate_reference_image_task ENTERED for user {user_id}")

    from app.services.image.comfyui_provider import ComfyUIProvider
    from app.services.image.prompt_builder import build_avatar_prompt
    from app.services.image.watermark import apply_watermark
    from app.database import supabase_admin
    from storage3.exceptions import StorageApiError
    import httpx

    try:
        # Fetch avatar using service role (no user JWT in background context)
        logger.error(f"[BG_TASK][STEP-0] Fetching avatar for user {user_id}")
        avatar_result = supabase_admin.from_("avatars").select("*").eq("user_id", user_id).execute()
        if not avatar_result.data:
            logger.error(f"Background task: no avatar found for user {user_id}")
            return

        avatar = avatar_result.data[0]
        logger.error(f"[BG_TASK][STEP-0] Avatar fetched OK: {avatar.get('id')}")

        # Step 1: Generate image via ComfyUI
        logger.error(f"[BG_TASK][STEP-1] Starting ComfyUI generation for user {user_id}")
        provider = ComfyUIProvider()
        prompt = build_avatar_prompt(
            avatar,
            "neutral background, natural light, full body visible, standing"
        )
        generated = await provider.generate(prompt)
        logger.error(f"[BG_TASK][STEP-1] ComfyUI generation complete, image_bytes={len(generated.image_bytes) if generated.image_bytes else 0}")

        # Step 2: Get image bytes (provider returns them directly)
        image_bytes = generated.image_bytes
        if not image_bytes:
            logger.error(f"[BG_TASK][STEP-2] image_bytes empty, downloading from URL")
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=120, write=30, pool=10)) as client:
                resp = await client.get(generated.url)
                resp.raise_for_status()
                image_bytes = resp.content
        logger.error(f"[BG_TASK][STEP-2] image_bytes ready: {len(image_bytes)} bytes")

        # Step 3: Apply watermark (compliance requirement -- TAKE IT DOWN Act)
        logger.error(f"[BG_TASK][STEP-3] Applying watermark")
        watermarked = apply_watermark(image_bytes)
        logger.error(f"[BG_TASK][STEP-3] Watermark applied: {len(watermarked)} bytes")

        # Step 4: Upload to Supabase Storage
        # Fixed path so the photo processor can always find the reference image
        storage_path = f"{user_id}/reference.jpg"
        logger.error(f"[BG_TASK][STEP-4] Ensuring bucket and uploading to {storage_path}")
        # Ensure bucket exists — startup creates it, but guard here for resilience
        try:
            supabase_admin.storage.create_bucket("photos", options={"public": False})
            logger.error("[BG_TASK][STEP-4] Created 'photos' storage bucket")
        except StorageApiError as bucket_err:
            bucket_err_str = str(bucket_err).lower()
            if "already exists" in bucket_err_str or "duplicate" in bucket_err_str:
                logger.error("[BG_TASK][STEP-4] 'photos' bucket already exists (expected)")
            else:
                logger.error(f"Background task: failed to ensure 'photos' bucket: {bucket_err}")
                return
        supabase_admin.storage.from_("photos").upload(
            storage_path,
            watermarked,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )
        logger.error(f"[BG_TASK][STEP-4] Upload complete for {storage_path}")

        # Step 5: Write storage path (NOT a signed URL) to the avatar row.
        # Storing the raw path ensures the reference image is accessible permanently.
        # GET /avatars/me generates a fresh signed URL at read time from this path.
        logger.error(f"[BG_TASK][STEP-5] Writing storage path to reference_image_url for user {user_id}")
        update_result = supabase_admin.from_("avatars").update(
            {"reference_image_url": storage_path}
        ).eq("user_id", user_id).execute()

        if not update_result.data:
            logger.error(f"Background task: failed to update reference_image_url for user {user_id}: update returned empty data")
            return

        logger.error(f"[BG_TASK][STEP-5] DB update successful. reference image path stored for user {user_id}")

    except asyncio.CancelledError:
        # CancelledError is BaseException, not Exception — must be caught explicitly.
        # This should not normally happen since we use asyncio.ensure_future() to decouple
        # the task from the request lifecycle, but we log it for observability if it does.
        logger.error(
            f"[BG_TASK] Background task CANCELLED for user {user_id} — "
            "this indicates unexpected task cancellation. reference_image_url was NOT written."
        )
        raise  # Re-raise CancelledError so the event loop handles it correctly
    except Exception as e:
        logger.error(
            f"Background task: reference image generation failed for user {user_id}: {e}\n"
            + traceback.format_exc()
        )
        # Do NOT re-raise -- background task failure must not crash the event loop


@router.post("", response_model=AvatarResponse)
async def create_avatar(
    body: AvatarCreate,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Create avatar for the authenticated user.
    One avatar per user enforced -- returns 400 if one already exists.
    Age must be >= 20 (enforced at DB level via CHECK constraint).
    """
    # Check if user already has an avatar (DB UNIQUE constraint also enforces this)
    existing = db.from_("avatars").select("id").eq("user_id", str(user.id)).execute()
    if existing.data:
        raise HTTPException(
            status_code=400,
            detail="Avatar already exists. One avatar per user in Phase 2.",
        )

    result = db.from_("avatars").insert({
        "user_id": str(user.id),
        "name": body.name,
        "age": body.age,
        "personality": body.personality,
        "physical_description": body.physical_description,
        "gender": body.gender,
        "nationality": body.nationality,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create avatar")

    return result.data[0]


@router.get("/me", response_model=AvatarResponse)
async def get_my_avatar(
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Get the authenticated user's avatar.

    If reference_image_url contains a raw Supabase Storage path (e.g. "{user_id}/reference.jpg")
    rather than a full URL, a fresh 1-hour signed URL is generated before returning so the
    frontend always receives a usable URL. This is the permanent-storage pattern: paths live
    in the DB forever; signed URLs are generated on demand at read time.
    """
    from app.database import supabase_admin as _admin

    result = db.from_("avatars").select("*").eq("user_id", str(user.id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No avatar found")

    avatar = result.data[0]

    # Re-sign if reference_image_url is a storage path (no scheme) rather than a full URL.
    ref = avatar.get("reference_image_url")
    if ref and not ref.startswith("http"):
        try:
            sign_response = (
                _admin.storage
                .from_("photos")
                .create_signed_url(ref, 3600)  # 1-hour signed URL at read time
            )
            fresh_url = (
                sign_response.get("signedURL")
                or sign_response.get("signedUrl")
                or sign_response.get("signed_url")
            )
            if fresh_url:
                avatar["reference_image_url"] = fresh_url
            else:
                logger.error(f"get_my_avatar: failed to sign path {ref!r} — sign_response={sign_response}")
        except Exception as sign_err:
            logger.error(f"get_my_avatar: error signing reference_image_url path {ref!r}: {sign_err}")

    return avatar


@router.patch("/me/persona")
async def update_persona(
    body: PersonaUpdateRequest,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Update the authenticated user's avatar persona.
    Clears session avatar cache so the new persona takes effect immediately.
    """
    result = db.from_("avatars").update(
        {"personality": body.personality.value}
    ).eq("user_id", str(user.id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="No avatar found")

    # Invalidate session avatar cache so next message picks up the new persona
    # (per RESEARCH.md Pitfall 5: cache is never auto-invalidated on persona update)
    session_store = get_session_store()
    await session_store.clear_avatar_cache(str(user.id))

    return {"personality": body.personality.value}


@router.post("/me/reference-image", status_code=202)
async def generate_reference_image(
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Kick off reference image generation for the user's avatar.

    Returns 202 immediately -- the actual ComfyUI generation (60-120s) runs as an
    independent asyncio Task. The client should poll GET /avatars/me every 3 seconds
    until avatar.reference_image_url is non-null.

    GAP-3 fix: previously this endpoint awaited provider.generate() synchronously,
    blocking the HTTP connection for 60-120s and triggering Nginx proxy_read_timeout (60s).

    BUG FIX (2026-03-02): previously used FastAPI BackgroundTasks which are tied to the
    request lifecycle via Starlette HTTPMiddleware (used internally by CORSMiddleware).
    When the HTTP connection closes after the 202 response, Starlette propagates
    asyncio.CancelledError into the background task at the first await point
    (asyncio.sleep inside _poll_and_download). CancelledError is BaseException (not
    Exception), so the except Exception block does not catch it — the task dies silently
    with zero log output and reference_image_url stays NULL forever.

    Fix: asyncio.ensure_future() schedules an independent Task that is NOT part of the
    request Task tree and cannot be cancelled by connection closure.
    """
    # Confirm avatar exists before queuing (fast DB check -- no timeout risk)
    avatar_result = db.from_("avatars").select("id").eq("user_id", str(user.id)).execute()
    if not avatar_result.data:
        raise HTTPException(status_code=404, detail="No avatar found -- create avatar first")

    # Clear any previous reference_image_url so polling correctly waits for the new one
    db.from_("avatars").update(
        {"reference_image_url": None}
    ).eq("user_id", str(user.id)).execute()

    # Schedule as an independent asyncio Task -- decoupled from request lifecycle.
    # asyncio.ensure_future() creates a Task on the running event loop that is NOT
    # a child of the current request Task and therefore cannot be cancelled on
    # connection close (unlike FastAPI BackgroundTasks with CORSMiddleware present).
    asyncio.ensure_future(_generate_reference_image_task(str(user.id)))

    return {"status": "generating"}
