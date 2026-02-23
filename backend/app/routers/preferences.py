from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_authed_supabase
from app.models.preferences import PhoneLinkRequest, PreferencesResponse

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
    }).execute()

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
