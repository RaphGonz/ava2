"""Google OAuth routes for Calendar connection.

GET /auth/google/connect?user_id={uuid}  — returns JSON with auth_url for user to click
GET /auth/google/callback?code={code}&state={user_id}  — exchanges code, stores tokens
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from app.services.google_auth.flow import get_auth_url, exchange_code_for_tokens

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/google", tags=["google-oauth"])


@router.get("/connect")
async def google_connect(user_id: str = Query(..., description="User UUID from Supabase auth")):
    """Return the Google OAuth consent URL.

    The WhatsApp bot sends this URL to the user when a calendar skill is triggered
    but no tokens exist for them: 'To use calendar features, tap: {url}'
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    try:
        auth_url = get_auth_url()
        # Append user_id as state param so callback knows which user to store tokens for
        separator = "&" if "?" in auth_url else "?"
        auth_url_with_state = f"{auth_url}{separator}state={user_id}"
        return {"auth_url": auth_url_with_state}
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail="Could not initiate Google auth")


@router.get("/callback", response_class=HTMLResponse)
async def google_callback(
    code: str = Query(...),
    state: str = Query(..., description="user_id passed through OAuth state"),
):
    """Handle Google OAuth callback. Exchanges code for tokens and stores them."""
    try:
        await exchange_code_for_tokens(user_id=state, code=code)
        return HTMLResponse(
            content="<html><body><h2>Google Calendar connected. You can close this tab.</h2></body></html>",
            status_code=200,
        )
    except Exception as e:
        logger.error(f"OAuth callback failed for user {state}: {e}")
        return HTMLResponse(
            content="<html><body><h2>Could not connect Google Calendar. Please try again.</h2></body></html>",
            status_code=400,
        )
