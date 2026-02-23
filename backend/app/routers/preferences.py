from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_authed_supabase

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.put("/whatsapp")
async def link_whatsapp(
    phone: str,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Link a WhatsApp phone number to the authenticated user's account.
    Phone must be in E.164 format: +1234567890

    Once linked, messages from this number on WhatsApp will be routed
    to this user's account.
    """
    # Validate E.164 format: must start with + followed by digits only
    if not phone.startswith("+") or not phone[1:].isdigit() or len(phone) < 8:
        raise HTTPException(
            status_code=400,
            detail="Phone must be in E.164 format: +1234567890",
        )

    result = db.from_("user_preferences").upsert({
        "user_id": str(user.id),
        "whatsapp_phone": phone,
    }).execute()

    return {"status": "linked", "phone": phone}


@router.get("/me")
async def get_preferences(
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """Get the authenticated user's preferences."""
    result = db.from_("user_preferences").select("*").eq("user_id", str(user.id)).execute()
    if not result.data:
        return {"user_id": str(user.id), "whatsapp_phone": None}
    return result.data[0]
