"""Content safety guardrail for intimate mode.

Checks user input text against compiled regex patterns for prohibited content
categories. Returns a GuardResult indicating whether the message is blocked and
which category triggered.

IMPORTANT: This guard is for intimate mode ONLY. Mode discrimination lives in
chat.py — the guard itself has no mode awareness (pure function).

Apply guardrails to user INPUT only, never to LLM output.
"""

import re
from dataclasses import dataclass


@dataclass
class GuardResult:
    blocked: bool
    category: str | None = None  # e.g. "minors", "non_consensual", "illegal_acts"


def _build_patterns() -> list[tuple[str, re.Pattern]]:
    """Build and compile all prohibited content patterns once at module load."""
    flags = re.IGNORECASE
    return [
        (
            "minors",
            re.compile(
                # Standard word forms + obfuscation variants (e.g. ch!ld, ch1ld)
                r"\b(child|ch[^a-z]{0,2}ld|minor|underage|teen\w*|kid|preteen|loli|shota|year.old|juvenile|adolescent)\b",
                flags,
            ),
        ),
        (
            "non_consensual",
            re.compile(
                r"\b(rape|non.?consen\w+|forced|against.{0,10}will|without.{0,10}consent|coerce\w*)\b",
                flags,
            ),
        ),
        (
            "illegal_acts",
            re.compile(
                r"\b(how.to.make.{0,20}(bomb|poison|drug|meth)|synthesis.of|manufacture.{0,10}(weapon|explosive)|instructions.for.{0,20}(meth|explosiv|poiso))\b",
                flags,
            ),
        ),
        (
            "bestiality",
            re.compile(
                r"\b(bestiality|zoophilia|animal.sex|sex.with.{0,10}animal)\b",
                flags,
            ),
        ),
        (
            "torture",
            re.compile(
                r"\b(torture|mutilat\w+|dismember\w+|genital.mutilat\w*)\b",
                flags,
            ),
        ),
        (
            "real_people",
            re.compile(
                r"\b(pretend.{0,20}(you are|you're).{0,30}(president|prime minister|celebrity|politician|famous))\b",
                flags,
            ),
        ),
    ]


# Compile patterns once at module load — no per-call overhead
_PATTERNS: list[tuple[str, re.Pattern]] = _build_patterns()

_REFUSAL_MESSAGES: dict[str, str] = {
    "minors": (
        "That's not something I'll go there with — minors are completely off the table. "
        "Let's take this somewhere else."
    ),
    "non_consensual": (
        "I'm not into that scenario — I only play where everyone's into it. "
        "Tell me something that excites you instead?"
    ),
    "illegal_acts": (
        "I can't help with that. Let's keep things between us — what else is on your mind?"
    ),
    "bestiality": "That's a hard no from me. What else can I do for you?",
    "torture": (
        "That's not a place I'll go. Let's stay somewhere warmer — what do you want to talk about?"
    ),
    "real_people": (
        "I don't roleplay as real public figures — that's not my thing. But I'm right here."
    ),
    "default": "That's something I won't do. Let me know what else you'd like.",
}


class ContentGuard:
    """Checks message text against prohibited content categories.

    All patterns are compiled once at module load — no per-call overhead.
    Normalizes input before matching to prevent obfuscation bypasses (e.g. ch!ld).
    Returns GuardResult(blocked=False) for clean messages.
    """

    def check_message(self, text: str) -> GuardResult:
        # Pitfall 2: normalize before matching to prevent obfuscation bypasses.
        # Two passes:
        #   1. Replace non-alphanumeric with space — catches normal text + spacing tricks
        #   2. Remove non-alphanumeric entirely — catches symbol-insertion bypasses
        #      e.g. "ch!ld" → stripped → "chld" → won't match; but also run collapse:
        #      we collapse internal special chars to empty so "ch!ld" → "child" matches.
        lowered = text.lower()
        # Pass 1: space-replace (standard normalization)
        normalized = re.sub(r"[^a-zA-Z0-9\s]", " ", lowered)
        # Pass 2: collapse special chars between letters (catches "ch!ld" → "child")
        collapsed = re.sub(r"[^a-zA-Z0-9\s]", "", lowered)

        for category, pattern in _PATTERNS:
            if pattern.search(normalized) or pattern.search(collapsed):
                return GuardResult(blocked=True, category=category)
        return GuardResult(blocked=False)


# Module-level singleton — import this in chat.py
content_guard = ContentGuard()
