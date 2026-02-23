from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user, get_authed_supabase
from app.models.message import MessageResponse
from typing import List

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=List[MessageResponse])
async def get_message_history(
    limit: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """Returns user's message history, newest first. RLS enforces isolation."""
    result = (
        db.from_("messages")
        .select("*")
        .eq("user_id", str(user.id))
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
