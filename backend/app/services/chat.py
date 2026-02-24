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
from openai import AsyncOpenAI
from app.services.skills import registry  # triggers eager skill registration via __init__
from app.services.skills.intent_classifier import classify_intent
from app.services.skills.calendar_skill import execute_pending_add, PendingCalendarAdd
from app.config import settings as _settings
from app.services.content_guard.guard import content_guard, _REFUSAL_MESSAGES
from app.services.crisis.detector import crisis_detector, CRISIS_RESPONSE

logger = logging.getLogger(__name__)

# Keywords that confirm a pending calendar conflict — lives here so it runs before
# intent classification, where 'yes' would otherwise be classified as 'chat'.
CALENDAR_CONFIRM_KEYWORDS = {"yes", "y", "yeah", "yep", "oui"}

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


async def _log_guardrail_trigger(user_id: str, category: str | None) -> None:
    """Log content guardrail trigger to audit_log. Non-fatal — DB failure is logged, not raised."""
    try:
        from app.database import supabase_admin
        supabase_admin.from_("audit_log").insert({
            "user_id": user_id,
            "event_type": "content_guardrail_triggered",
            "event_category": "moderation",
            "action": "block",
            "resource_type": "message",
            "event_data": {"category": category},
            "result": "blocked",
        }).execute()
    except Exception as e:
        logger.error(f"Guardrail audit log write failed for user {user_id}: {e}")


async def _log_crisis(user_id: str, triggering_phrases: list[str]) -> None:
    """Log crisis detection to audit_log (separate event_type from guardrail). Non-fatal."""
    try:
        from app.database import supabase_admin
        supabase_admin.from_("audit_log").insert({
            "user_id": user_id,
            "event_type": "crisis_detected",
            "event_category": "moderation",
            "action": "pivot",
            "resource_type": "message",
            "event_data": {"triggering_phrases": triggering_phrases},
            "result": "crisis_response_sent",
        }).execute()
    except Exception as e:
        logger.error(f"Crisis audit log write failed for user {user_id}: {e}")


class ChatService:
    """
    Stateless orchestrator — all state lives in SessionStore.

    Designed to be instantiated once as a module-level singleton and called
    from webhook.py and future chat.py router. Thread-safe via SessionStore's asyncio.Lock.
    """

    def __init__(self, llm: LLMProvider, session_store: SessionStore | None = None):
        self._llm = llm
        self._store = session_store or get_session_store()
        # Intent classifier uses a separate AsyncOpenAI client — lightweight fast model call
        self._openai_client = AsyncOpenAI(api_key=_settings.openai_api_key, max_retries=1)
        self._intent_model = _settings.llm_model  # reuse configured model

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

        # --- Calendar conflict confirmation gate ---
        # Must run BEFORE intent classification: 'yes' is classified as 'chat' by the
        # LLM classifier, so it must be caught here as a conflict confirmation instead.
        if session.pending_calendar_add is not None:
            stripped = incoming_text.strip().lower()
            pending = session.pending_calendar_add
            session.pending_calendar_add = None  # clear regardless of answer
            if stripped in CALENDAR_CONFIRM_KEYWORDS:
                reply = await execute_pending_add(pending)
                await self._store.append_message(
                    user_id, session.mode, {"role": "user", "content": incoming_text}
                )
                await self._store.append_message(
                    user_id, session.mode, {"role": "assistant", "content": reply}
                )
                return reply
            # else: user declined — fall through to normal intent routing

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

        # --- Normal message: skill dispatch (secretary) or LLM (intimate) ---
        current_mode = session.mode
        history = list(session.history[current_mode])  # snapshot before append

        # Secretary mode: classify intent and dispatch to skill if applicable.
        # Intimate mode: bypass intent classification entirely — go straight to LLM.
        if current_mode == ConversationMode.SECRETARY:
            try:
                intent = await classify_intent(
                    self._openai_client, incoming_text, self._intent_model
                )
                if intent.skill != "chat":
                    user_tz = avatar.get("timezone", "UTC") if avatar else "UTC"
                    skill = registry.get(intent.skill)
                    if skill is not None:
                        # Pass session so calendar_add can store PendingCalendarAdd on conflict
                        skill_reply = await skill.handle(user_id, intent, user_tz, session=session)
                        await self._store.append_message(
                            user_id, current_mode, {"role": "user", "content": incoming_text}
                        )
                        await self._store.append_message(
                            user_id, current_mode, {"role": "assistant", "content": skill_reply}
                        )
                        return skill_reply
            except Exception as e:
                logger.error(f"Skill dispatch failed for user {user_id}, falling back to LLM: {e}")
                # Fall through to LLM on any skill dispatch error — never break the chat

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
