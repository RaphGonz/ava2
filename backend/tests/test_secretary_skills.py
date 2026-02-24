"""Tests for secretary skill dispatch in ChatService.

Tests confirm:
1. Secretary mode: intent classifier is called; skill handler is dispatched for non-chat intents
2. Intimate mode: intent classifier is NOT called; LLM is called directly
3. Skill dispatch errors fall back to LLM gracefully
4. 'chat' intent falls through to LLM even in secretary mode
5. Calendar conflict confirmation: 'yes' after a conflict warning creates the event
6. Calendar conflict rejection: any other reply cancels and routes normally

Uses unittest.mock.AsyncMock to avoid real API calls.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chat import ChatService
from app.services.session.models import ConversationMode
from app.services.skills.registry import ParsedIntent
from app.services.skills.calendar_skill import PendingCalendarAdd
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_avatar(name: str = "Ava", personality: str = "caring", tz: str = "UTC") -> dict:
    return {"id": "avatar-uuid", "name": name, "personality": personality, "timezone": tz}


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.complete = AsyncMock(return_value="LLM response")
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
# Tests: secretary mode dispatch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_secretary_calendar_add_dispatches_to_skill(mock_llm, mock_store):
    """calendar_add intent routes to CalendarSkill, not LLM."""
    store, session = mock_store
    service = ChatService(llm=mock_llm, session_store=store)

    calendar_intent = ParsedIntent(
        skill="calendar_add",
        raw_text="Add team standup Tuesday at 3pm",
        extracted_title="team standup",
        extracted_date="Tuesday at 3pm",
    )

    with patch(
        "app.services.chat.classify_intent", new=AsyncMock(return_value=calendar_intent)
    ):
        mock_skill = MagicMock()
        mock_skill.handle = AsyncMock(return_value="Added: Team standup · Tue · 3:00pm")

        with patch("app.services.chat.registry.get", return_value=mock_skill):
            reply = await service.handle_message(
                user_id="user-123",
                incoming_text="Add team standup Tuesday at 3pm",
                avatar=make_avatar(),
            )

    assert reply == "Added: Team standup · Tue · 3:00pm"
    mock_skill.handle.assert_called_once()
    # session kwarg must be passed so conflicts can be stored
    call_kwargs = mock_skill.handle.call_args.kwargs
    assert "session" in call_kwargs, "skill.handle() must receive session= kwarg"
    mock_llm.complete.assert_not_called()  # LLM must NOT be called


@pytest.mark.asyncio
async def test_secretary_research_dispatches_to_skill(mock_llm, mock_store):
    """research intent routes to ResearchSkill, not LLM."""
    store, session = mock_store
    service = ChatService(llm=mock_llm, session_store=store)

    research_intent = ParsedIntent(
        skill="research",
        raw_text="What is quantum entanglement?",
        query="quantum entanglement",
    )

    with patch(
        "app.services.chat.classify_intent", new=AsyncMock(return_value=research_intent)
    ):
        mock_skill = MagicMock()
        mock_skill.handle = AsyncMock(return_value="Quantum entanglement is a phenomenon...\n\nSource: https://example.com")

        with patch("app.services.chat.registry.get", return_value=mock_skill):
            reply = await service.handle_message(
                user_id="user-123",
                incoming_text="What is quantum entanglement?",
                avatar=make_avatar(),
            )

    assert "Quantum entanglement" in reply
    mock_skill.handle.assert_called_once()
    mock_llm.complete.assert_not_called()


@pytest.mark.asyncio
async def test_secretary_chat_intent_falls_through_to_llm(mock_llm, mock_store):
    """'chat' intent bypasses skills and routes to LLM."""
    store, session = mock_store
    service = ChatService(llm=mock_llm, session_store=store)

    chat_intent = ParsedIntent(skill="chat", raw_text="How are you?")

    with patch(
        "app.services.chat.classify_intent", new=AsyncMock(return_value=chat_intent)
    ):
        reply = await service.handle_message(
            user_id="user-123",
            incoming_text="How are you?",
            avatar=make_avatar(),
        )

    assert reply == "LLM response"
    mock_llm.complete.assert_called_once()


@pytest.mark.asyncio
async def test_intimate_mode_bypasses_intent_classifier(mock_llm, mock_store):
    """Intimate mode must NOT call intent classifier — goes straight to LLM."""
    store, session = mock_store
    session.mode = ConversationMode.INTIMATE  # Set to intimate mode
    service = ChatService(llm=mock_llm, session_store=store)

    with patch(
        "app.services.chat.classify_intent", new=AsyncMock()
    ) as mock_classify:
        reply = await service.handle_message(
            user_id="user-123",
            incoming_text="I feel so connected to you",
            avatar=make_avatar(),
        )

    mock_classify.assert_not_called()  # CRITICAL: classifier must not run in intimate mode
    assert reply == "LLM response"


@pytest.mark.asyncio
async def test_skill_dispatch_error_falls_back_to_llm(mock_llm, mock_store):
    """Skill dispatch failure (e.g., network error) falls back to LLM — never crashes."""
    store, session = mock_store
    service = ChatService(llm=mock_llm, session_store=store)

    failing_intent = ParsedIntent(skill="research", raw_text="What is dark matter?", query="dark matter")

    with patch(
        "app.services.chat.classify_intent", new=AsyncMock(return_value=failing_intent)
    ):
        mock_skill = MagicMock()
        mock_skill.handle = AsyncMock(side_effect=Exception("Tavily API down"))

        with patch("app.services.chat.registry.get", return_value=mock_skill):
            reply = await service.handle_message(
                user_id="user-123",
                incoming_text="What is dark matter?",
                avatar=make_avatar(),
            )

    # Falls back to LLM, not an error message
    assert reply == "LLM response"
    mock_llm.complete.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: calendar conflict confirmation gate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_yes_confirms_pending_calendar_add(mock_llm, mock_store):
    """When pending_calendar_add is set and user replies 'yes', event is created."""
    store, session = mock_store
    now = datetime.now(timezone.utc)
    # Simulate a stored conflict pending confirmation
    session.pending_calendar_add = PendingCalendarAdd(
        user_id="user-123",
        title="Team standup",
        start_dt=now,
        end_dt=now,
        user_tz="UTC",
    )
    service = ChatService(llm=mock_llm, session_store=store)

    with patch(
        "app.services.chat.execute_pending_add",
        new=AsyncMock(return_value="Added: Team standup · Tue · 3:00pm")
    ) as mock_execute:
        with patch("app.services.chat.classify_intent", new=AsyncMock()) as mock_classify:
            reply = await service.handle_message(
                user_id="user-123",
                incoming_text="yes",
                avatar=make_avatar(),
            )

    assert reply == "Added: Team standup · Tue · 3:00pm"
    mock_execute.assert_called_once()
    # Intent classifier must NOT be called — gate resolves before classifier
    mock_classify.assert_not_called()
    mock_llm.complete.assert_not_called()
    # pending_calendar_add must be cleared after handling
    assert session.pending_calendar_add is None


@pytest.mark.asyncio
async def test_oui_confirms_pending_calendar_add(mock_llm, mock_store):
    """French 'oui' also confirms a pending calendar add."""
    store, session = mock_store
    now = datetime.now(timezone.utc)
    session.pending_calendar_add = PendingCalendarAdd(
        user_id="user-123",
        title="Réunion d'équipe",
        start_dt=now,
        end_dt=now,
        user_tz="Europe/Paris",
    )
    service = ChatService(llm=mock_llm, session_store=store)

    with patch(
        "app.services.chat.execute_pending_add",
        new=AsyncMock(return_value="Added: Réunion d'équipe · Tue · 3:00pm")
    ) as mock_execute:
        reply = await service.handle_message(
            user_id="user-123",
            incoming_text="oui",
            avatar=make_avatar(),
        )

    assert "Réunion" in reply
    mock_execute.assert_called_once()


@pytest.mark.asyncio
async def test_non_yes_cancels_pending_calendar_add(mock_llm, mock_store):
    """Any non-yes reply clears the pending add and routes the message normally."""
    store, session = mock_store
    now = datetime.now(timezone.utc)
    session.pending_calendar_add = PendingCalendarAdd(
        user_id="user-123",
        title="Team standup",
        start_dt=now,
        end_dt=now,
        user_tz="UTC",
    )
    service = ChatService(llm=mock_llm, session_store=store)

    chat_intent = ParsedIntent(skill="chat", raw_text="no")
    with patch(
        "app.services.chat.execute_pending_add", new=AsyncMock()
    ) as mock_execute:
        with patch(
            "app.services.chat.classify_intent", new=AsyncMock(return_value=chat_intent)
        ):
            reply = await service.handle_message(
                user_id="user-123",
                incoming_text="no",
                avatar=make_avatar(),
            )

    # execute_pending_add must NOT be called
    mock_execute.assert_not_called()
    # Message routes normally to LLM (chat intent)
    assert reply == "LLM response"
    mock_llm.complete.assert_called_once()
    # pending_calendar_add must be cleared
    assert session.pending_calendar_add is None
