"""Tests for SessionStore — history isolation, overflow, and reset."""
import pytest
from app.services.session.store import SessionStore, SessionState
from app.services.session.models import ConversationMode


@pytest.fixture
def store():
    return SessionStore()


class TestSessionCreation:
    @pytest.mark.asyncio
    async def test_new_user_gets_empty_state(self, store):
        state = await store.get_or_create("user-123")
        assert state.mode == ConversationMode.SECRETARY
        assert state.history[ConversationMode.SECRETARY] == []
        assert state.history[ConversationMode.INTIMATE] == []

    @pytest.mark.asyncio
    async def test_same_user_returns_same_state(self, store):
        state1 = await store.get_or_create("user-abc")
        state2 = await store.get_or_create("user-abc")
        assert state1 is state2


class TestHistoryIsolation:
    @pytest.mark.asyncio
    async def test_secretary_message_stays_in_secretary(self, store):
        msg = {"role": "user", "content": "Hello"}
        await store.append_message("user-1", ConversationMode.SECRETARY, msg)
        state = await store.get_or_create("user-1")
        assert len(state.history[ConversationMode.SECRETARY]) == 1
        assert len(state.history[ConversationMode.INTIMATE]) == 0

    @pytest.mark.asyncio
    async def test_intimate_message_stays_in_intimate(self, store):
        msg = {"role": "user", "content": "Private message"}
        await store.append_message("user-2", ConversationMode.INTIMATE, msg)
        state = await store.get_or_create("user-2")
        assert len(state.history[ConversationMode.INTIMATE]) == 1
        assert len(state.history[ConversationMode.SECRETARY]) == 0


class TestHistoryOverflow:
    @pytest.mark.asyncio
    async def test_overflow_drops_oldest_messages(self, store):
        for i in range(45):
            await store.append_message(
                "user-overflow",
                ConversationMode.SECRETARY,
                {"role": "user", "content": f"Message {i}"},
            )
        state = await store.get_or_create("user-overflow")
        history = state.history[ConversationMode.SECRETARY]
        assert len(history) <= SessionStore.MAX_HISTORY_MESSAGES
        # Newest messages should be retained
        assert history[-1]["content"] == "Message 44"


class TestModeSwitch:
    @pytest.mark.asyncio
    async def test_switch_changes_mode(self, store):
        await store.switch_mode("user-3", ConversationMode.INTIMATE)
        state = await store.get_or_create("user-3")
        assert state.mode == ConversationMode.INTIMATE

    @pytest.mark.asyncio
    async def test_switch_clears_pending(self, store):
        state = await store.get_or_create("user-4")
        state.pending_switch_to = ConversationMode.INTIMATE  # simulate pending
        await store.switch_mode("user-4", ConversationMode.INTIMATE)
        state = await store.get_or_create("user-4")
        assert state.pending_switch_to is None


class TestSessionReset:
    @pytest.mark.asyncio
    async def test_reset_clears_all_history(self, store):
        await store.append_message(
            "user-5", ConversationMode.SECRETARY, {"role": "user", "content": "Hi"}
        )
        await store.reset_session("user-5")
        state = await store.get_or_create("user-5")
        assert state.history[ConversationMode.SECRETARY] == []
        assert state.mode == ConversationMode.SECRETARY
