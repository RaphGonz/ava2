"""
Replicate API image provider using FLUX 1.1 Pro.
Calls the Replicate REST API directly via httpx to avoid the replicate library's
Pydantic v2 type-inference bug on models with a 'previous' field.
Satisfies ImageProvider Protocol via structural typing.
"""
import asyncio
import logging
import httpx
from app.config import settings
from app.services.image.base import GeneratedImage

logger = logging.getLogger(__name__)

FLUX_MODEL_VERSION = "black-forest-labs/flux-1.1-pro"
REPLICATE_API_URL = "https://api.replicate.com/v1/models/{model}/predictions"
POLL_INTERVAL = 2.0   # seconds between status checks
POLL_TIMEOUT  = 300   # seconds before giving up


class ReplicateProvider:
    """
    Calls Replicate REST API with FLUX 1.1 Pro directly via httpx.
    Returns GeneratedImage with temporary CDN URL (~1 hour expiry).
    """

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "2:3",
    ) -> GeneratedImage:
        api_token = settings.replicate_api_token
        if not api_token:
            raise RuntimeError("REPLICATE_API_TOKEN is not set in .env")

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Prefer": "wait",  # ask Replicate to wait up to 60s before returning
        }
        payload = {
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "output_format": "jpg",
                "output_quality": 90,
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Submit prediction
            url = REPLICATE_API_URL.format(model=FLUX_MODEL_VERSION)
            resp = await client.post(url, json=payload, headers=headers)
            if resp.is_error:
                logger.error(f"Replicate API error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            prediction = resp.json()

            # If already completed (Prefer: wait honoured), return immediately
            if prediction.get("status") == "succeeded":
                return self._extract(prediction, prompt)

            # Otherwise poll until done
            poll_url = prediction["urls"]["get"]
            elapsed = 0.0
            while elapsed < POLL_TIMEOUT:
                await asyncio.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL
                poll_resp = await client.get(poll_url, headers=headers)
                poll_resp.raise_for_status()
                prediction = poll_resp.json()
                status = prediction.get("status")
                if status == "succeeded":
                    return self._extract(prediction, prompt)
                if status in ("failed", "canceled"):
                    raise RuntimeError(
                        f"Replicate prediction {status}: {prediction.get('error')}"
                    )

            raise TimeoutError(f"Replicate prediction timed out after {POLL_TIMEOUT}s")

    def _extract(self, prediction: dict, prompt: str) -> GeneratedImage:
        output = prediction.get("output")
        if isinstance(output, list):
            url = str(output[0])
        elif isinstance(output, str):
            url = output
        else:
            raise RuntimeError(f"Unexpected Replicate output format: {output!r}")
        logger.info(f"Replicate generated image: {url[:80]}...")
        return GeneratedImage(url=url, model=FLUX_MODEL_VERSION, prompt=prompt)
