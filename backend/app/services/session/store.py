import asyncio
from dataclasses import dataclass, field
from typing import Any
from app.services.session.models import ConversationMode, Message


@dataclass
class SessionState:
    mode: ConversationMode = ConversationMode.SECRETARY
    history: dict = field(
        default_factory=lambda: {
            ConversationMode.SECRETARY: [],
            ConversationMode.INTIMATE: [],
        }
    )
    pending_switch_to: ConversationMode | None = None  # clarification gate: mode switch
    pending_calendar_add: Any | None = None  # clarification gate: calendar conflict confirmation


class SessionStore:
    """In-memory per-user conversation state. asyncio.Lock guards all mutations.

    WARNING: In-memory only. Requires single uvicorn worker (--workers 1).
    Multi-worker deployments need a Redis-backed SessionStore implementation.
    """

    MAX_HISTORY_MESSAGES = 40  # silently drop oldest; context window overflow strategy

    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, user_id: str) -> SessionState:
        async with self._lock:
            if user_id not in self._sessions:
                self._sessions[user_id] = SessionState()
            return self._sessions[user_id]

    async def append_message(self, user_id: str, mode: ConversationMode, message: Message) -> None:
        async with self._lock:
            state = self._sessions.setdefault(user_id, SessionState())
            history = state.history[mode]
            history.append(message)
            if len(history) > self.MAX_HISTORY_MESSAGES:
                excess = len(history) - self.MAX_HISTORY_MESSAGES
                state.history[mode] = history[excess:]

    async def switch_mode(self, user_id: str, new_mode: ConversationMode) -> None:
        """Switch mode. Clears pending_switch_to. History per mode preserved."""
        async with self._lock:
            state = self._sessions.setdefault(user_id, SessionState())
            state.mode = new_mode
            state.pending_switch_to = None

    async def reset_session(self, user_id: str) -> None:
        """Explicit reset — clears all history and returns to SECRETARY mode."""
        async with self._lock:
            self._sessions[user_id] = SessionState()

    async def clear_avatar_cache(self, user_id: str) -> None:
        """Clear the avatar cache for a user so the next message re-fetches from DB.

        Called after PATCH /avatars/me/persona so persona changes take effect immediately.
        No-op if the user has no active session.
        """
        async with self._lock:
            state = self._sessions.get(user_id)
            if state is not None and hasattr(state, "_avatar_cache"):
                object.__setattr__(state, "_avatar_cache", None)


_session_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Module-level singleton getter. One store per process."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
