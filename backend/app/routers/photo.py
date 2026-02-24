"""
Photo delivery router — POST /photos/signed-url.

Generates a 24-hour Supabase Storage signed URL for a photo stored in the private
'photos' bucket. The signed URL IS the auth token (per CONTEXT.md decision: no login
required to view, token = auth, 24h expiry).

Note: Photo GENERATION is Phase 7 (INTM-03). Phase 6 provides the delivery
infrastructure that Phase 7 will wire up.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies import get_current_user
from app.database import supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/photos", tags=["photos"])

PHOTO_BUCKET = "photos"
SIGNED_URL_EXPIRY_SECONDS = 86400  # 24 hours


class SignedUrlRequest(BaseModel):
    photo_path: str  # e.g. "user-id/photo-filename.jpg"


@router.post("/signed-url")
async def create_photo_signed_url(
    body: SignedUrlRequest,
    user=Depends(get_current_user),
):
    """
    Generate a 24-hour signed URL for a photo in the private 'photos' Supabase Storage bucket.

    The signed URL is self-contained auth — no separate token table needed.
    Anyone with the link can view the photo for 24 hours.

    Called by Phase 7 image generation when a photo is ready for delivery.
    """
    try:
        response = (
            supabase_admin.storage
            .from_(PHOTO_BUCKET)
            .create_signed_url(body.photo_path, SIGNED_URL_EXPIRY_SECONDS)
        )
        signed_url = response.get("signedURL") or response.get("signed_url")
        if not signed_url:
            raise HTTPException(status_code=500, detail="Failed to generate signed URL")
        return {"signed_url": signed_url, "expires_in_seconds": SIGNED_URL_EXPIRY_SECONDS}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signed URL generation failed for path {body.photo_path}: {e}")
        raise HTTPException(status_code=500, detail="Photo URL generation failed")
