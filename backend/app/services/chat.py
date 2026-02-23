"""
ChatService — orchestrates mode detection, session management, and LLM calls.

Flow for each incoming message:
  1. Fetch session state (get_or_create)
  2. Cache avatar in session if not yet cached
  3. Run ModeSwitchDetector on incoming text
  4. Route based on detection result:
     a. exact/fuzzy -> switch mode (or acknowledge already-in-mode)
     b. ambiguous -> set pending_switch_to, return clarification question
     c. pending resolution -> handle "yes"/"no" confirmation
     d. none -> call LLM with current mode history + system prompt
  5. Append user message and assistant reply to session history
  6. Return reply text (caller sends via WhatsApp or HTTP)
"""
import logging
from dataclasses import dataclass, field
from app.services.session.store import SessionStore, SessionState, get_session_store
from app.services.session.models import ConversationMode, Message
from app.services.mode_detection.detector import detect_mode_switch, DetectionResult
from app.services.llm.base import LLMProvider
from app.services.llm.prompts import secretary_prompt, intimate_prompt

logger = logging.getLogger(__name__)

# Mode switch confirmation messages (per CONTEXT.md decisions)
SWITCH_TO_INTIMATE_MSG = "Switching to private mode — just us now 💬"
SWITCH_TO_SECRETARY_MSG = "Back to work mode."
ALREADY_INTIMATE_MSG = "We're already in private mode 😉"
ALREADY_SECRETARY_MSG = "We're already in work mode."
CLARIFICATION_TO_INTIMATE_MSG = (
    "Did you mean to switch to private mode? Reply 'yes' or use /intimate."
)
CLARIFICATION_TO_SECRETARY_MSG = (
    "Did you mean to switch back to work mode? Reply 'yes' or use /stop."
)
ONBOARDING_PROMPT = (
    "You haven't set up your Ava profile yet — visit ava.example.com to get started."
)
LLM_ERROR_MSG = "I'm having trouble thinking right now — try again in a moment."


class ChatService:
    """
    Stateless orchestrator — all state lives in SessionStore.

    Designed to be instantiated once as a module-level singleton and called
    from webhook.py and future chat.py router. Thread-safe via SessionStore's asyncio.Lock.
    """

    def __init__(self, llm: LLMProvider, session_store: SessionStore | None = None):
        self._llm = llm
        self._store = session_store or get_session_store()

    async def handle_message(
        self,
        user_id: str,
        incoming_text: str,
        avatar: dict | None,
    ) -> str:
        """
        Process one incoming message and return the reply text.

        Args:
            user_id: Authenticated user's UUID.
            incoming_text: Raw text from WhatsApp or HTTP.
            avatar: Avatar row dict (name, personality) or None if not set up.

        Returns:
            Reply text to send back to the user.
        """
        # Guard: user has no avatar — send onboarding prompt
        if avatar is None:
            return ONBOARDING_PROMPT

        session = await self._store.get_or_create(user_id)

        # Cache avatar in session state on first message (avoid DB call per message)
        if not hasattr(session, "_avatar_cache") or session._avatar_cache is None:
            object.__setattr__(session, "_avatar_cache", avatar)

        avatar_name = avatar.get("name", "Ava")
        personality = avatar.get("personality", "caring")

        # --- Clarification gate resolution ---
        if session.pending_switch_to is not None:
            stripped = incoming_text.strip().lower()
            if stripped in ("yes", "y", "yeah", "yep"):
                new_mode = session.pending_switch_to
                await self._store.switch_mode(user_id, new_mode)
                if new_mode == ConversationMode.INTIMATE:
                    return SWITCH_TO_INTIMATE_MSG
                else:
                    return SWITCH_TO_SECRETARY_MSG
            else:
                # User ignored clarification — cancel pending switch, route normally
                session.pending_switch_to = None

        # --- Mode switch detection ---
        detection = detect_mode_switch(incoming_text, session.mode)

        if detection.confidence in ("exact", "fuzzy"):
            target = detection.target
            if target == session.mode:
                # Already in this mode — acknowledge playfully
                if session.mode == ConversationMode.INTIMATE:
                    return ALREADY_INTIMATE_MSG
                else:
                    return ALREADY_SECRETARY_MSG
            # Switch mode
            await self._store.switch_mode(user_id, target)
            if target == ConversationMode.INTIMATE:
                return SWITCH_TO_INTIMATE_MSG
            else:
                return SWITCH_TO_SECRETARY_MSG

        if detection.confidence == "ambiguous":
            session.pending_switch_to = detection.target
            if detection.target == ConversationMode.INTIMATE:
                return CLARIFICATION_TO_INTIMATE_MSG
            else:
                return CLARIFICATION_TO_SECRETARY_MSG

        # --- Normal message: call LLM ---
        current_mode = session.mode
        history = list(session.history[current_mode])  # snapshot before append

        if current_mode == ConversationMode.SECRETARY:
            system_prompt = secretary_prompt(avatar_name, personality)
        else:
            system_prompt = intimate_prompt(avatar_name, personality)

        user_message: Message = {"role": "user", "content": incoming_text}

        try:
            reply = await self._llm.complete(history + [user_message], system_prompt)
        except Exception as e:
            logger.error(f"LLM call failed for user {user_id}: {e}")
            reply = LLM_ERROR_MSG

        # Append both turns to session history (mode-isolated)
        await self._store.append_message(user_id, current_mode, user_message)
        await self._store.append_message(
            user_id, current_mode, {"role": "assistant", "content": reply}
        )

        return reply
