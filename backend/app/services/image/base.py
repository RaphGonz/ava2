"""
ImageProvider Protocol — ARCH-03 compliance.
Mirrors LLMProvider structural pattern from Phase 3 (backend/app/services/llm/base.py).
Any class with async generate() satisfies this Protocol without inheritance.
"""
from typing import Protocol, runtime_checkable
from dataclasses import dataclass


@dataclass
class GeneratedImage:
    url: str     # Temporary Replicate CDN URL — download immediately, expires ~1h
    model: str   # e.g. "black-forest-labs/flux-1.1-pro"
    prompt: str  # Full prompt used (for audit log)


@runtime_checkable
class ImageProvider(Protocol):
    """
    Structural interface for image generation providers (ARCH-03).
    Swapping providers = swap config + new concrete class. No inheritance needed.
    """
    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "2:3",
    ) -> GeneratedImage:
        ...
