"""Skill registry for secretary mode.

Uses Python Protocol (structural typing) for the Skill interface — consistent with
LLMProvider in backend/app/services/llm/base.py. No ABC or inheritance required.

New skills can be added by:
1. Implementing a class with the Skill.handle() signature
2. Calling register() at module import time in the skill module
3. No routing logic changes needed
"""
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ParsedIntent:
    """Normalized intent object passed to all skill handlers.

    Produced by classify_intent() and consumed by Skill.handle().
    Fields beyond skill/raw_text are intent-specific and may be None.
    """

    skill: str           # "calendar_add" | "calendar_view" | "research" | "chat"
    raw_text: str        # original user message
    extracted_date: str | None = None   # for calendar intents (e.g. "mardi à 15h")
    extracted_title: str | None = None  # for calendar intents (e.g. "Team standup")
    query: str | None = None            # for research intents


@runtime_checkable
class Skill(Protocol):
    """Interface every skill must satisfy (structural typing — no inheritance needed).

    Any class with an async handle() method matching this signature satisfies Skill.
    To add a new skill: implement handle(), call register() at module import time.
    """

    async def handle(self, user_id: str, intent: ParsedIntent, user_tz: str) -> str:
        """Process a classified intent and return a reply string.

        Args:
            user_id: Authenticated user identifier.
            intent: Parsed and classified intent from classify_intent().
            user_tz: User's timezone string (e.g. "America/New_York").
        Returns:
            Reply text to send to the user.
        """
        ...


_REGISTRY: dict[str, Skill] = {}


def register(skill_name: str, skill: Skill) -> None:
    """Register a skill handler. Call at module import time in each skill module."""
    _REGISTRY[skill_name] = skill


def get(skill_name: str) -> Skill | None:
    """Retrieve a registered skill by name. Returns None if not found."""
    return _REGISTRY.get(skill_name)


def list_skills() -> list[str]:
    """Return list of registered skill names. For debugging and testing."""
    return list(_REGISTRY.keys())
