from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_authed_supabase
from app.models.avatar import AvatarCreate, AvatarResponse, PersonaUpdateRequest
from app.services.session.store import get_session_store

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
