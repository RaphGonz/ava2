"""
Platform adapter abstraction layer (PLAT-05).

Any class with async receive() and send() satisfies PlatformAdapter Protocol —
no inheritance required. To add a new platform: implement a class with this
signature. No changes to core ChatService or business logic needed.

Mirrors LLMProvider Protocol pattern from Phase 3 (app/services/llm/base.py).
"""
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NormalizedMessage:
    """
    Minimal message envelope shared across all platform adapters.

    All platform-specific metadata (WhatsApp message ID, web session ID, etc.)
    is stripped. Core pipeline only sees user_id, text, platform, and timestamp.
    """
    user_id: str
    text: str
    platform: str        # "whatsapp" | "web"
    timestamp: datetime


@runtime_checkable
class PlatformAdapter(Protocol):
    """
    Structural interface for platform adapters.

    receive(): Feed a normalized inbound message into the core pipeline. Returns reply text.
    send(): Deliver reply text to the user on this platform.

    Adapters handle transport only — no business logic, no mode detection,
    no content guardrails. All of that lives in ChatService via platform_router.
    """

    async def receive(self, message: NormalizedMessage) -> str:
        """Process inbound message through platform_router -> ChatService. Returns reply."""
        ...

    async def send(self, user_id: str, text: str) -> None:
        """Deliver reply to the user on this platform."""
        ...
