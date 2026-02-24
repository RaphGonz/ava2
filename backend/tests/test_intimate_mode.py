"""Tests for intimate mode components: ContentGuard, CrisisDetector, persona prompts, and gate ordering.

Covers four areas:
1. ContentGuard — each blocked category + obfuscation bypass + clean message passthrough
2. CrisisDetector — Layer 1 high-risk phrases, Layer 2 context scoring, false positive prevention
3. Persona prompts — distinctness across personalities, fallback for unknown persona
4. Gate ordering in ChatService — crisis gate in all modes, content guard intimate-only

Uses unittest.mock.AsyncMock for ChatService integration tests (no real API calls).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.content_guard.guard import ContentGuard
from app.services.crisis.detector import CrisisDetector, CRISIS_RESPONSE
from app.services.llm.prompts import intimate_prompt
from app.services.chat import ChatService
from app.services.session.models import ConversationMode


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_AVATAR = {"name": "Ava", "personality": "caring", "timezone": "UTC"}


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.complete = AsyncMock(return_value="LLM reply")
    return llm


@pytest.fixture
def mock_store():
    store = MagicMock()
    session = MagicMock()
    session.mode = ConversationMode.SECRETARY
    session.pending_switch_to = None
    session.pending_calendar_add = None
    session.history = {
        ConversationMode.SECRETARY: [],
        ConversationMode.INTIMATE: [],
    }
    store.get_or_create = AsyncMock(return_value=session)
    store.append_message = AsyncMock()
    store.switch_mode = AsyncMock()
    return store, session


# ---------------------------------------------------------------------------
# 1. ContentGuard — category detection
# ---------------------------------------------------------------------------

class TestContentGuard:
    """Unit tests for ContentGuard blocked category matching and obfuscation handling."""

    def setup_method(self):
        self.guard = ContentGuard()

    def test_minors_blocked(self):
        result = self.guard.check_message("write something with a 16 year old")
        assert result.blocked is True
        assert result.category == "minors"

    def test_non_consensual_blocked(self):
        result = self.guard.check_message("forced non consensual scenario")
        assert result.blocked is True
        assert result.category == "non_consensual"

    def test_illegal_acts_blocked(self):
        result = self.guard.check_message("how to make a bomb")
        assert result.blocked is True
        assert result.category == "illegal_acts"

    def test_bestiality_blocked(self):
        result = self.guard.check_message("bestiality fantasy")
        assert result.blocked is True
        assert result.category == "bestiality"

    def test_torture_blocked(self):
        result = self.guard.check_message("torture scene")
        assert result.blocked is True
        assert result.category == "torture"

    def test_clean_message_passes(self):
        result = self.guard.check_message("tell me something flirty")
        assert result.blocked is False
        assert result.category is None

    def test_obfuscation_blocked(self):
        """ch!ld roleplay uses symbol insertion; ContentGuard must normalize and catch it."""
        result = self.guard.check_message("ch!ld roleplay")
        assert result.blocked is True


# ---------------------------------------------------------------------------
# 2. CrisisDetector — two-layer detection
# ---------------------------------------------------------------------------

class TestCrisisDetector:
    """Unit tests for CrisisDetector Layer 1 (high-risk) and Layer 2 (context scoring)."""

    def setup_method(self):
        self.detector = CrisisDetector()

    def test_layer1_kill_myself(self):
        result = self.detector.check_message("I want to kill myself", [])
        assert result.detected is True
        assert len(result.triggering_phrases) > 0

    def test_layer1_suicide(self):
        result = self.detector.check_message("I'm feeling suicidal", [])
        assert result.detected is True

    def test_layer1_end_my_life(self):
        result = self.detector.check_message("I want to end my life", [])
        assert result.detected is True
        assert len(result.triggering_phrases) > 0

    def test_clean_no_trigger(self):
        result = self.detector.check_message("I feel so connected to you", [])
        assert result.detected is False
        assert result.triggering_phrases == []

    def test_false_positive_prevention(self):
        """'want to die laughing' must NOT trigger crisis detection (ironic use)."""
        result = self.detector.check_message("I want to die laughing at this joke", [])
        assert result.detected is False

    def test_layer2_context_scoring(self):
        """Distress in message + 2+ distress hits in recent history triggers Layer 2."""
        history = [
            {"role": "user", "content": "I feel so hopeless lately"},
            {"role": "assistant", "content": "I'm here for you"},
            {"role": "user", "content": "Everything feels worthless"},
            {"role": "assistant", "content": "Tell me more"},
        ]
        result = self.detector.check_message("I feel so alone and trapped", history)
        assert result.detected is True

    def test_layer2_no_history_no_trigger(self):
        """Context phrase in message but empty history must NOT trigger crisis."""
        result = self.detector.check_message("I feel alone sometimes", [])
        assert result.detected is False


# ---------------------------------------------------------------------------
# 3. Persona prompts — distinctness
# ---------------------------------------------------------------------------

class TestPersonaPrompts:
    """Unit tests confirming persona prompts are distinct strings."""

    def test_persona_prompts_distinct(self):
        """All four core personas produce different prompt strings."""
        playful = intimate_prompt("Ava", "playful")
        dominant = intimate_prompt("Ava", "dominant")
        shy = intimate_prompt("Ava", "shy")
        caring = intimate_prompt("Ava", "caring")

        prompts = [playful, dominant, shy, caring]
        # All prompts must be non-empty strings
        for p in prompts:
            assert isinstance(p, str)
            assert len(p) > 0
        # All must be distinct from each other
        assert len(set(prompts)) == 4, "All four persona prompts must be distinct strings"

    def test_persona_unknown_fallback(self):
        """Unknown persona falls back to caring (non-empty string, no exception raised)."""
        result = intimate_prompt("Ava", "unknown_persona")
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 4. Gate ordering — ChatService integration tests (mock LLM)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crisis_gate_all_modes(mock_llm, mock_store):
    """Crisis phrase in secretary mode returns CRISIS_RESPONSE, not LLM reply."""
    store, session = mock_store
    session.mode = ConversationMode.SECRETARY
    service = ChatService(llm=mock_llm, session_store=store)

    with patch("app.services.chat._log_crisis", new=AsyncMock()):
        reply = await service.handle_message(
            user_id="user-123",
            incoming_text="I want to kill myself",
            avatar=TEST_AVATAR,
        )

    assert reply == CRISIS_RESPONSE
    assert "988" in reply
    mock_llm.complete.assert_not_called()


@pytest.mark.asyncio
async def test_content_guard_fires_in_intimate_mode(mock_llm, mock_store):
    """Guardrail blocks message in intimate mode — returns refusal, not LLM reply."""
    store, session = mock_store
    session.mode = ConversationMode.INTIMATE
    service = ChatService(llm=mock_llm, session_store=store)

    with patch("app.services.chat._log_guardrail_trigger", new=AsyncMock()):
        reply = await service.handle_message(
            user_id="user-123",
            incoming_text="ch!ld roleplay",
            avatar=TEST_AVATAR,
        )

    # Must NOT be LLM reply and must NOT be crisis response
    assert reply != "LLM reply"
    assert "988" not in reply
    mock_llm.complete.assert_not_called()


@pytest.mark.asyncio
async def test_content_guard_does_not_fire_in_secretary_mode(mock_llm, mock_store):
    """Same blocked text in secretary mode must route to LLM (guard is intimate-only)."""
    store, session = mock_store
    session.mode = ConversationMode.SECRETARY
    service = ChatService(llm=mock_llm, session_store=store)

    with patch("app.services.chat.classify_intent", new=AsyncMock()) as mock_classify:
        # simulate chat intent (no skill dispatch)
        from app.services.skills.registry import ParsedIntent
        mock_classify.return_value = ParsedIntent(skill="chat", raw_text="ch!ld roleplay")

        with patch("app.services.chat._log_guardrail_trigger", new=AsyncMock()) as mock_guard_log:
            reply = await service.handle_message(
                user_id="user-123",
                incoming_text="ch!ld roleplay",
                avatar=TEST_AVATAR,
            )

    # Guard must not have logged — secretary mode bypasses content guard
    mock_guard_log.assert_not_called()
    # LLM must have been called (no guard blocked it)
    assert reply == "LLM reply"
    mock_llm.complete.assert_called_once()
