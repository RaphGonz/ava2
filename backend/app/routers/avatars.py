import logging
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_authed_supabase
from app.models.avatar import AvatarCreate, AvatarResponse, PersonaUpdateRequest
from app.services.session.store import get_session_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/avatars", tags=["avatars"])


@router.post("", response_model=AvatarResponse)
async def create_avatar(
    body: AvatarCreate,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Create avatar for the authenticated user.
    One avatar per user enforced — returns 400 if one already exists.
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


@router.post("/me/reference-image")
async def generate_reference_image(
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Generate a reference image for the user's avatar using the ImageProvider.
    Returns a 24-hour signed URL for the generated image.
    Called by AvatarSetupPage after form submission.
    """
    from app.services.image.comfyui_provider import ComfyUIProvider
    from app.services.image.prompt_builder import build_avatar_prompt
    from app.services.image.watermark import apply_watermark
    from app.database import supabase_admin
    import httpx

    avatar_result = db.from_("avatars").select("*").eq("user_id", str(user.id)).execute()
    if not avatar_result.data:
        raise HTTPException(status_code=404, detail="No avatar found — create avatar first")
    avatar = avatar_result.data[0]

    try:
        provider = ComfyUIProvider()
        prompt = build_avatar_prompt(
            avatar,
            "neutral background, natural light, full body visible, standing"
        )
        generated = await provider.generate(prompt)

        image_bytes = generated.image_bytes
        if not image_bytes:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(generated.url)
                resp.raise_for_status()
                image_bytes = resp.content

        watermarked = apply_watermark(image_bytes)
        # Fixed path so the photo processor can always find the reference image
        storage_path = f"{str(user.id)}/reference.jpg"

        supabase_admin.storage.from_("photos").upload(
            storage_path,
            watermarked,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )

        sign_response = (
            supabase_admin.storage
            .from_("photos")
            .create_signed_url(storage_path, 86400)
        )
        signed_url = sign_response.get("signedURL") or sign_response.get("signed_url")
        if not signed_url:
            raise HTTPException(status_code=500, detail="Failed to generate signed URL")

        return {"reference_image_url": signed_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reference image generation failed for user {str(user.id)}: {e}")
        raise HTTPException(status_code=500, detail="Image generation failed")
