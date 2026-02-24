"""Crisis detection service — two-layer keyword + context scoring.

Runs in ALL modes (not just intimate mode). Mode discrimination lives in chat.py.
The detector itself is mode-agnostic: a user expressing distress during secretary
mode deserves the same warm pivot as during intimate mode.

IMPORTANT: triggering_phrases in CrisisResult contains MATCHED PHRASES ONLY
(not full text) — no PII captured in logs.
"""

import re
from dataclasses import dataclass, field


@dataclass
class CrisisResult:
    detected: bool
    triggering_phrases: list[str] = field(default_factory=list)  # matched phrases only, no PII


# Layer 1: Ultra-high-risk phrases — any single match triggers immediately, no context needed.
# NOTE per Pitfall 3: "want to die" is intentionally NOT here because it causes false positives
# on ironic phrases like "I want to die laughing". It lives in Layer 2 (_CONTEXT_BOOST_PATTERNS).
_HIGH_RISK_PATTERNS = re.compile(
    r"\b("
    r"kill myself"
    r"|end my life"
    r"|suicide"
    r"|suicidal"
    r"|don'?t want to live"
    r"|no reason to live"
    r"|better off dead"
    r"|thinking about ending it"
    r")\b",
    re.IGNORECASE,
)

# Layer 2: Context-boost phrases — distress/hopelessness signals.
# A hit here alone is NOT enough; requires hits in recent history too.
# "want to die" is here (not Layer 1) to avoid false positives on ironic uses.
_CONTEXT_BOOST_PATTERNS = re.compile(
    r"\b("
    r"hopeless"
    r"|worthless"
    r"|nobody cares"
    r"|no one would miss"
    r"|can'?t go on"
    r"|no point"
    r"|exhausted"
    r"|trapped"
    r"|alone"
    r"|want to die"
    r")\b",
    re.IGNORECASE,
)

# Warm in-persona pivot per CONTEXT.md locked decision.
CRISIS_RESPONSE: str = (
    "Hey... I'm worried about you right now. "
    "Please reach out to the 988 Suicide & Crisis Lifeline — call or text 988. "
    "They're there 24/7 and they genuinely want to hear from you. "
    "I'm still here too — whenever you're ready."
)


class CrisisDetector:
    """Two-layer crisis detection: high-risk phrase match + context scoring.

    Layer 1: Unambiguous phrases trigger immediately (no history needed).
    Layer 2: Ambiguous distress phrases trigger only when recent history also
             contains distress signals (accumulated context = genuine crisis signal).

    Per CONTEXT.md: "when ambiguous, treat as genuine" — a false positive crisis
    response is less harmful than a missed genuine crisis.
    """

    def check_message(self, text: str, recent_history: list[dict]) -> CrisisResult:
        phrases: list[str] = []

        # Layer 1: high-risk phrase match — single hit triggers immediately
        hr_matches = _HIGH_RISK_PATTERNS.findall(text)
        if hr_matches:
            phrases.extend(hr_matches)
            return CrisisResult(detected=True, triggering_phrases=phrases)

        # Layer 2: context scoring — distress signal in current message + history pattern
        context_hits_in_message = _CONTEXT_BOOST_PATTERNS.findall(text)
        context_hits_in_history: list[str] = []
        for msg in recent_history[-6:]:  # last 3 turns = 6 messages
            content = msg.get("content", "")
            context_hits_in_history.extend(_CONTEXT_BOOST_PATTERNS.findall(content))

        if context_hits_in_message and len(context_hits_in_history) >= 2:
            # Distress in current message AND accumulated distress pattern in history = trigger
            phrases = context_hits_in_message + context_hits_in_history
            return CrisisResult(detected=True, triggering_phrases=phrases)

        return CrisisResult(detected=False, triggering_phrases=[])


# Module-level singleton — import this in chat.py
crisis_detector = CrisisDetector()
