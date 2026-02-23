from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.config import settings

router = APIRouter(prefix="/dev", tags=["dev"])

# Templates directory is two levels up from this file: routers/ -> app/ -> backend/ -> templates/
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


@router.get("/auth", response_class=HTMLResponse)
async def dev_auth():
    """
    Serve the minimal barebones HTML auth test UI.

    Only available in development mode. Returns 404 in production.
    Used to verify that signup and signin work end-to-end in a browser.
    """
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")

    auth_html = _TEMPLATES_DIR / "auth.html"
    return HTMLResponse(content=auth_html.read_text(encoding="utf-8"))


@router.get("/onboarding", response_class=HTMLResponse)
async def dev_onboarding():
    """
    Serve the minimal barebones HTML onboarding test UI.

    Only available in development mode. Returns 404 in production.
    Used to test avatar creation and phone linking end-to-end in a browser.
    """
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")

    onboarding_html = _TEMPLATES_DIR / "onboarding.html"
    return HTMLResponse(content=onboarding_html.read_text(encoding="utf-8"))
