import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
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
    from app.services.image.comfyui_provider import ComfyUIProvider
    from app.services.image.prompt_builder import build_avatar_prompt
    from app.services.image.watermark import apply_watermark
    from app.database import supabase_admin
    import httpx

    try:
        # Fetch avatar using service role (no user JWT in background context)
        avatar_result = supabase_admin.from_("avatars").select("*").eq("user_id", user_id).execute()
        if not avatar_result.data:
            logger.error(f"Background task: no avatar found for user {user_id}")
            return

        avatar = avatar_result.data[0]

        # Step 1: Generate image via ComfyUI
        provider = ComfyUIProvider()
        prompt = build_avatar_prompt(
            avatar,
            "neutral background, natural light, full body visible, standing"
        )
        generated = await provider.generate(prompt)

        # Step 2: Get image bytes (provider returns them directly)
        image_bytes = generated.image_bytes
        if not image_bytes:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=120, write=30, pool=10)) as client:
                resp = await client.get(generated.url)
                resp.raise_for_status()
                image_bytes = resp.content

        # Step 3: Apply watermark (compliance requirement -- TAKE IT DOWN Act)
        watermarked = apply_watermark(image_bytes)

        # Step 4: Upload to Supabase Storage
        # Fixed path so the photo processor can always find the reference image
        storage_path = f"{user_id}/reference.jpg"
        supabase_admin.storage.from_("photos").upload(
            storage_path,
            watermarked,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )

        # Step 5: Create 24-hour signed URL
        sign_response = (
            supabase_admin.storage
            .from_("photos")
            .create_signed_url(storage_path, 86400)
        )
        signed_url = sign_response.get("signedURL") or sign_response.get("signed_url")
        if not signed_url:
            logger.error(f"Background task: failed to create signed URL for user {user_id}")
            return

        # Step 6: Write reference_image_url to the avatar row
        # The frontend polls GET /avatars/me -- when this field is non-null, polling stops.
        update_result = supabase_admin.from_("avatars").update(
            {"reference_image_url": signed_url}
        ).eq("user_id", user_id).execute()

        if not update_result.data:
            logger.error(f"Background task: failed to update reference_image_url for user {user_id}")
            return

        logger.info(f"Background task: reference image ready for user {user_id}")

    except Exception as e:
        logger.error(f"Background task: reference image generation failed for user {user_id}: {e}")
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
    """Get the authenticated user's avatar."""
    result = db.from_("avatars").select("*").eq("user_id", str(user.id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No avatar found")
    return result.data[0]


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
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Kick off reference image generation for the user's avatar.

    Returns 202 immediately -- the actual ComfyUI generation (60-120s) runs as a
    FastAPI BackgroundTask. The client should poll GET /avatars/me every 3 seconds
    until avatar.reference_image_url is non-null.

    GAP-3 fix: previously this endpoint awaited provider.generate() synchronously,
    blocking the HTTP connection for 60-120s and triggering Nginx proxy_read_timeout (60s).
    """
    # Confirm avatar exists before queuing (fast DB check -- no timeout risk)
    avatar_result = db.from_("avatars").select("id").eq("user_id", str(user.id)).execute()
    if not avatar_result.data:
        raise HTTPException(status_code=404, detail="No avatar found -- create avatar first")

    # Clear any previous reference_image_url so polling correctly waits for the new one
    db.from_("avatars").update(
        {"reference_image_url": None}
    ).eq("user_id", str(user.id)).execute()

    # Schedule the full pipeline as a background task -- returns immediately
    background_tasks.add_task(_generate_reference_image_task, str(user.id))

    return {"status": "generating"}
