from dataclasses import dataclass
from rapidfuzz import process, fuzz
from app.services.session.models import ConversationMode

# Extend these lists to add new trigger phrases without touching detection logic
INTIMATE_PHRASES = [
    "i'm alone", "im alone", "let's be alone", "lets be alone",
    "private", "i am alone", "just us", "we're alone", "were alone",
]
SECRETARY_PHRASES = [
    "stop", "back to work", "secretary mode", "work mode",
    "that's enough", "thats enough", "let's stop", "lets stop",
]
SLASH_COMMANDS: dict[str, ConversationMode] = {
    "/intimate": ConversationMode.INTIMATE,
    "/secretary": ConversationMode.SECRETARY,
    "/stop": ConversationMode.SECRETARY,
}

FUZZY_THRESHOLD = 75     # score >= this: confident match, confirm before switching
AMBIGUOUS_THRESHOLD = 50  # score in [50, 75): ambiguous, ask for clarification
MAX_WORDS_FOR_FUZZY = 10  # guard: long sentences with trigger words should not fire


@dataclass
class DetectionResult:
    target: ConversationMode | None  # None = not a mode switch attempt
    confidence: str                   # "exact" | "fuzzy" | "ambiguous" | "none"


def detect_mode_switch(text: str, current_mode: ConversationMode) -> DetectionResult:
    """
    Classify incoming text as a mode switch request or normal message.

    Detection order:
    1. Exact slash command match (highest confidence, immune to message length)
    2. Long message guard: skip fuzzy for messages > MAX_WORDS_FOR_FUZZY words
    3. Fuzzy phrase match via rapidfuzz token_set_ratio (handles natural language)

    Returns:
        DetectionResult with:
        - confidence="exact"     -> slash command, act immediately
        - confidence="fuzzy"     -> score >= FUZZY_THRESHOLD, confirm before switching
        - confidence="ambiguous" -> score in [AMBIGUOUS_THRESHOLD, FUZZY_THRESHOLD), clarify
        - confidence="none"      -> normal message, route to LLM
    """
    stripped = text.strip().lower()

    # Stage 1: Exact slash command (immune to message length)
    if stripped in SLASH_COMMANDS:
        return DetectionResult(target=SLASH_COMMANDS[stripped], confidence="exact")

    # Stage 2: Long message guard — only slash commands match for long inputs
    word_count = len(stripped.split())
    if word_count > MAX_WORDS_FOR_FUZZY:
        return DetectionResult(target=None, confidence="none")

    # Stage 3: Fuzzy phrase match
    intimate_match = process.extractOne(stripped, INTIMATE_PHRASES, scorer=fuzz.token_set_ratio)
    secretary_match = process.extractOne(stripped, SECRETARY_PHRASES, scorer=fuzz.token_set_ratio)

    best_target: ConversationMode | None = None
    best_score = 0
    if intimate_match and intimate_match[1] > best_score:
        best_score = intimate_match[1]
        best_target = ConversationMode.INTIMATE
    if secretary_match and secretary_match[1] > best_score:
        best_score = secretary_match[1]
        best_target = ConversationMode.SECRETARY

    if best_score >= FUZZY_THRESHOLD:
        return DetectionResult(target=best_target, confidence="fuzzy")
    if best_score >= AMBIGUOUS_THRESHOLD:
        return DetectionResult(target=best_target, confidence="ambiguous")

    return DetectionResult(target=None, confidence="none")
