"""
ImageProvider Protocol — ARCH-03 compliance.
Mirrors LLMProvider structural pattern from Phase 3 (backend/app/services/llm/base.py).
Any class with async generate() satisfies this Protocol without inheritance.
"""
from typing import Protocol, runtime_checkable
from dataclasses import dataclass


@dataclass
class GeneratedImage:
    url: str            # CDN URL to download from (empty string if image_bytes is set)
    model: str          # e.g. "comfyui-qwen" or "black-forest-labs/flux-1.1-pro"
    prompt: str         # Full prompt used (for audit log)
    image_bytes: bytes | None = None  # Pre-downloaded bytes (set by ComfyUIProvider)


@runtime_checkable
class ImageProvider(Protocol):
    """
    Structural interface for image generation providers (ARCH-03).
    Swapping providers = swap config + new concrete class. No inheritance needed.
    reference_image_url is optional — providers that don't support i2i ignore it.
    """
    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "2:3",
        reference_image_url: str | None = None,
    ) -> GeneratedImage:
        ...
