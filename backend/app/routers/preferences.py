from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_authed_supabase
from app.models.preferences import PhoneLinkRequest, PreferencesResponse, PreferencesPatchRequest
from app.config import settings

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.put("/whatsapp")
async def link_whatsapp(
    body: PhoneLinkRequest,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Link a WhatsApp phone number to the authenticated user's account.
    Phone must be in E.164 format: +1234567890 (+ followed by 7-15 digits).

    Once linked, messages from this number on WhatsApp will be routed
    to this user's account. Pydantic validates E.164 before the DB write.
    """
    db.from_("user_preferences").upsert({
        "user_id": str(user.id),
        "whatsapp_phone": body.phone,
    }, on_conflict="user_id").execute()

    # Send welcome template to initiate the WhatsApp conversation
    if settings.whatsapp_access_token and settings.whatsapp_phone_number_id:
        try:
            from app.services.whatsapp import send_whatsapp_template
            await send_whatsapp_template(
                phone_number_id=settings.whatsapp_phone_number_id,
                to=body.phone,
                template_name="welcome",
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Welcome template failed for {body.phone}: {e}")

    return {"status": "linked", "phone": body.phone}


@router.get("/", response_model=PreferencesResponse)
async def get_preferences(
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """Get the authenticated user's preferences. Returns 404 if no preferences row exists."""
    result = db.from_("user_preferences").select("*").eq("user_id", str(user.id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No preferences found")
    return result.data[0]


@router.patch("/", response_model=PreferencesResponse)
async def update_preferences(
    body: PreferencesPatchRequest,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Update user preferences. Only provided fields are updated (PATCH semantics).
    Returns the full updated preferences row.
    """
    patch = body.model_dump(exclude_none=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")

    db.from_("user_preferences").upsert({
        "user_id": str(user.id),
        **patch,
    }, on_conflict="user_id").execute()

    result = db.from_("user_preferences").select("*").eq("user_id", str(user.id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Preferences not found after update")
    return result.data[0]
