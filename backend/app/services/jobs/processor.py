"""
BullMQ photo job processor — called by the Worker for each 'generate_photo' job.

Delivery strategy:
  - Web: Insert assistant photo message into messages table. Frontend polls /chat/history.
  - WhatsApp: Send signed URL link via Meta WhatsApp API (PLAT-03 — no inline NSFW).

Full pipeline per job:
  1. Build prompt from avatar fields + scene description
  2. Call ComfyUI Cloud API (image-to-image if reference exists, else text-to-image)
     — 4-step flow: POST /api/prompt → poll /api/job/{id}/status →
       GET /api/history_v2/{id} → GET /api/view (download)
  3. Image bytes returned directly by ComfyUIProvider
  4. Apply Pillow watermark (compliance requirement)
  5. Upload watermarked JPEG to Supabase Storage: photos/{user_id}/{job_id}.jpg
  6. Audit log (compliance)
  7. Deliver to user via channel-appropriate method:
       Web: store [PHOTO_PATH] storage path in message; GET /chat/history re-signs at read time
       WhatsApp: generate a fresh 1-hour signed URL at delivery time
  8. On all-retries-exhausted: notify user of failure
"""
import logging
import httpx
from app.services.image.comfyui_provider import ComfyUIProvider
from app.services.image.prompt_builder import build_avatar_prompt
from app.services.image.watermark import apply_watermark
from app.database import supabase_admin

logger = logging.getLogger(__name__)

PHOTO_BUCKET = "photos"
WHATSAPP_SIGNED_URL_TTL = 3600  # 1 hour — WhatsApp links are one-shot, short TTL is fine

_image_provider = ComfyUIProvider()

PHOTO_FAILURE_MSG = (
    "I wasn't able to send you a photo right now — please try again later."
)


async def _deliver_web(user_id: str, avatar: dict, storage_path: str) -> None:
    """Store photo as assistant message in messages table. Frontend polls /chat/history.

    Stores the raw Supabase Storage path using the [PHOTO_PATH] marker instead of a
    pre-signed URL. GET /chat/history rewrites [PHOTO_PATH] tokens to fresh signed URLs
    at read time so photos remain accessible permanently (no 24h expiry).
    """
    # [PHOTO_PATH]path[/PHOTO_PATH] is a storage path marker — chat history endpoint
    # converts this to a fresh signed URL before sending to the frontend.
    content = f"[PHOTO_PATH]{storage_path}[/PHOTO_PATH]"
    avatar_id = avatar.get("id") if avatar else None
    supabase_admin.from_("messages").insert({
        "user_id": user_id,
        "avatar_id": avatar_id,
        "channel": "web",
        "role": "assistant",
        "content": content,
    }).execute()


async def _deliver_whatsapp(user_id: str, storage_path: str) -> None:
    """Send a fresh signed URL link via WhatsApp (PLAT-03 — no inline NSFW images on WhatsApp).

    Generates a fresh 1-hour signed URL at delivery time from the raw storage path.
    WhatsApp links are one-shot (the user clicks immediately), so a short TTL is fine here.
    The storage path lives permanently in Supabase Storage; new signed URLs can always be
    generated on demand.
    """
    from app.services.whatsapp import send_whatsapp_message
    from app.config import settings

    # Generate a fresh short-lived signed URL for WhatsApp delivery
    sign_response = (
        supabase_admin.storage
        .from_(PHOTO_BUCKET)
        .create_signed_url(storage_path, WHATSAPP_SIGNED_URL_TTL)
    )
    signed_url = sign_response.get("signedURL") or sign_response.get("signed_url")
    if not signed_url:
        logger.error(f"_deliver_whatsapp: failed to sign path {storage_path!r} — sign_response={sign_response}")
        return

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

    message = f"Here's your photo (link valid 1h): {signed_url}"
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
        # Step 1: Build prompt from all avatar fields
        prompt = build_avatar_prompt(avatar, scene_description)
        logger.debug(f"Prompt ({len(prompt)} chars): {prompt[:120]}...")

        # Step 2: Get reference image signed URL for image-to-image generation
        ref_sign = (
            supabase_admin.storage
            .from_("photos")
            .create_signed_url(f"{user_id}/reference.jpg", 3600)
        )
        reference_image_url = ref_sign.get("signedURL") or ref_sign.get("signed_url")

        # Step 3: Generate via ComfyUI Cloud (image-to-image if reference exists)
        generated = await _image_provider.generate(
            prompt, reference_image_url=reference_image_url
        )

        # Step 4: Get image bytes (ComfyUI returns bytes directly)
        if generated.image_bytes:
            image_bytes = generated.image_bytes
        else:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(generated.url)
                resp.raise_for_status()
                image_bytes = resp.content
        logger.info(f"Got {len(image_bytes)} bytes from ComfyUI")

        # Step 5: Apply visible watermark (compliance requirement)
        watermarked_bytes = apply_watermark(image_bytes)

        # Step 6: Upload to Supabase Storage private bucket
        storage_path = f"{user_id}/{job_id}.jpg"
        supabase_admin.storage.from_(PHOTO_BUCKET).upload(
            storage_path,
            watermarked_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )
        logger.info(f"Uploaded to Supabase Storage: {storage_path}")

        # Step 7: Audit log — compliance (image generation tracking per CONTEXT.md)
        # Note: signed URL generation removed from this step. The storage path is permanent;
        # signed URLs are generated on demand at read time (web) or delivery time (WhatsApp).
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

        # Step 7b: Emit to usage_events for admin dashboard (ADMN-02)
        # audit_log write above is kept — both writes happen independently
        try:
            supabase_admin.from_("usage_events").insert({
                "user_id": user_id,
                "event_type": "photo_generated",
                "metadata": {"job_id": job_id, "channel": channel},
            }).execute()
        except Exception as exc:
            logger.error("Failed to emit photo_generated usage event: %s", exc)

        # Step 8: Deliver to user via channel using the permanent storage path.
        # _deliver_web stores the path in message content (re-signed at read time).
        # _deliver_whatsapp generates a fresh signed URL at delivery time.
        if channel == "whatsapp":
            await _deliver_whatsapp(user_id, storage_path)
        else:
            await _deliver_web(user_id, avatar, storage_path)

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
