"""
Replicate API image provider using FLUX 1.1 Pro.
Satisfies ImageProvider Protocol via structural typing.
"""
import logging
from app.services.image.base import GeneratedImage

logger = logging.getLogger(__name__)

FLUX_MODEL = "black-forest-labs/flux-1.1-pro"


class ReplicateProvider:
    """
    Calls Replicate async_run() with FLUX 1.1 Pro.
    Returns GeneratedImage with temporary CDN URL.

    IMPORTANT: URL expires ~1 hour. Worker must download immediately.
    """

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "2:3",
    ) -> GeneratedImage:
        import replicate  # lazy import — only needed at call time, not at class definition
        output = await replicate.async_run(
            FLUX_MODEL,
            input={
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "output_format": "jpeg",
                "output_quality": 90,
            },
        )
        # replicate v1.0+: output is a FileOutput or list; str() gives the CDN URL
        url = str(output) if not isinstance(output, list) else str(output[0])
        logger.info(f"Replicate generated image: {url[:80]}...")
        return GeneratedImage(url=url, model=FLUX_MODEL, prompt=prompt)
