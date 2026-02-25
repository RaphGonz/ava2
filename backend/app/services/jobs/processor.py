"""
BullMQ photo job processor — called by the Worker for each 'generate_photo' job.

Delivery strategy:
  - Web: Insert assistant photo message into messages table. Frontend polls /chat/history.
  - WhatsApp: Send signed URL link via Meta WhatsApp API (PLAT-03 — no inline NSFW).

Full pipeline per job:
  1. Build FLUX prompt from avatar fields + scene description
  2. Call Replicate FLUX API -> temporary CDN URL
  3. Download image bytes via httpx (download immediately — URL expires ~1h)
  4. Apply Pillow watermark (compliance requirement per CONTEXT.md)
  5. Upload watermarked JPEG to Supabase Storage: photos/{user_id}/{job_id}.jpg
  6. Generate 24-hour Supabase signed URL
  7. Audit log (compliance)
  8. Deliver to user via channel-appropriate method
  9. On all-retries-exhausted: notify user of failure
"""
import logging
import httpx
from app.services.image.replicate_provider import ReplicateProvider
from app.services.image.prompt_builder import build_avatar_prompt
from app.services.image.watermark import apply_watermark
from app.database import supabase_admin

logger = logging.getLogger(__name__)

PHOTO_BUCKET = "photos"
SIGNED_URL_EXPIRY = 86400  # 24 hours

_image_provider = ReplicateProvider()

PHOTO_FAILURE_MSG = (
    "I wasn't able to send you a photo right now — please try again later."
)


async def _deliver_web(user_id: str, avatar: dict, signed_url: str) -> None:
    """Store photo as assistant message in messages table. Frontend polls /chat/history."""
    # [PHOTO]url[/PHOTO] is a frontend render hint — ChatBubble renders it as <img>
    content = f"[PHOTO]{signed_url}[/PHOTO]"
    avatar_id = avatar.get("id") if avatar else None
    supabase_admin.from_("messages").insert({
        "user_id": user_id,
        "avatar_id": avatar_id,
        "channel": "web",
        "role": "assistant",
        "content": content,
    }).execute()


async def _deliver_whatsapp(user_id: str, signed_url: str) -> None:
    """Send signed URL link via WhatsApp (PLAT-03 — no inline NSFW images on WhatsApp)."""
    from app.services.whatsapp import send_whatsapp_message
    from app.config import settings

    result = (
        supabase_admin
        .from_("user_preferences")
        .select("whatsapp_phone")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    phone = (result.data or {}).get("whatsapp_phone")
    if not phone:
        logger.warning(f"No WhatsApp phone for user {user_id} — cannot deliver photo")
        return

    message = f"Here's your photo (link valid 24h): {signed_url}"
    await send_whatsapp_message(
        phone_number_id=settings.whatsapp_phone_number_id,
        to=phone,
        text=message,
    )


async def process_photo_job(job, token: str | None = None) -> None:
    """
    BullMQ Worker processor function.
    Receives job.data: {user_id, scene_description, avatar, channel}.

    On success: delivers photo to user via channel.
    On final failure: sends user a failure notification.
    BullMQ handles retries automatically per attempts/backoff config in queue.py.
    """
    data = job.data
    user_id: str = data["user_id"]
    scene_description: str = data["scene_description"]
    avatar: dict = data["avatar"]
    channel: str = data.get("channel", "web")
    job_id: str = str(job.id)

    logger.info(f"Processing photo job {job_id} for user {user_id} channel={channel}")

    try:
        # Step 1: Build FLUX prompt from all avatar fields
        prompt = build_avatar_prompt(avatar, scene_description)
        logger.debug(f"FLUX prompt ({len(prompt)} chars): {prompt[:120]}...")

        # Step 2: Generate via Replicate FLUX
        generated = await _image_provider.generate(prompt, aspect_ratio="2:3")
        logger.info(f"Replicate image URL: {generated.url[:80]}")

        # Step 3: Download immediately (URL expires ~1h — RESEARCH.md Pitfall 1)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(generated.url)
            resp.raise_for_status()
            image_bytes = resp.content
        logger.info(f"Downloaded {len(image_bytes)} bytes from Replicate")

        # Step 4: Apply visible watermark (compliance requirement)
        watermarked_bytes = apply_watermark(image_bytes)

        # Step 5: Upload to Supabase Storage private bucket
        storage_path = f"{user_id}/{job_id}.jpg"
        supabase_admin.storage.from_(PHOTO_BUCKET).upload(
            storage_path,
            watermarked_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )
        logger.info(f"Uploaded to Supabase Storage: {storage_path}")

        # Step 6: Generate Supabase signed URL (24h expiry)
        sign_response = (
            supabase_admin.storage
            .from_(PHOTO_BUCKET)
            .create_signed_url(storage_path, SIGNED_URL_EXPIRY)
        )
        signed_url = sign_response.get("signedURL") or sign_response.get("signed_url")
        if not signed_url:
            raise ValueError("Supabase Storage did not return a signed URL")
        logger.info(f"Signed URL generated (24h expiry)")

        # Step 7: Audit log — compliance (image generation tracking per CONTEXT.md)
        try:
            supabase_admin.from_("audit_log").insert({
                "user_id": user_id,
                "event_type": "photo_generated",
                "event_category": "image_generation",
                "action": "generate",
                "resource_type": "photo",
                "event_data": {
                    "prompt": prompt[:500],
                    "model": generated.model,
                    "storage_path": storage_path,
                    "job_id": job_id,
                },
                "result": "success",
            }).execute()
        except Exception as e:
            logger.warning(f"Audit log write failed (non-fatal): {e}")

        # Step 8: Deliver to user via channel
        if channel == "whatsapp":
            await _deliver_whatsapp(user_id, signed_url)
        else:
            await _deliver_web(user_id, avatar, signed_url)

        logger.info(f"Photo job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Photo job {job_id} failed (attempt {job.attemptsMade + 1}): {e}")

        # Notify user only on last attempt (all retries exhausted)
        max_attempts = job.opts.get("attempts", 3) if job.opts else 3
        if job.attemptsMade >= max_attempts - 1:
            logger.warning(f"All retries exhausted for job {job_id} — sending failure notification")
            try:
                if channel == "whatsapp":
                    await _deliver_whatsapp(user_id, PHOTO_FAILURE_MSG)
                else:
                    supabase_admin.from_("messages").insert({
                        "user_id": user_id,
                        "avatar_id": avatar.get("id") if avatar else None,
                        "channel": "web",
                        "role": "assistant",
                        "content": PHOTO_FAILURE_MSG,
                    }).execute()
            except Exception as notify_err:
                logger.error(f"Failure notification also failed for user {user_id}: {notify_err}")

        raise  # Re-raise so BullMQ records failure and triggers retry
