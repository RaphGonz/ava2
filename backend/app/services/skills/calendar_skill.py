"""Calendar skill for secretary mode.

Handles two intents:
  - calendar_add (SECR-01): parse date/title, check conflicts, create event, confirm
  - calendar_view (SECR-02): list upcoming events as formatted bullet list

Uses Google Calendar API v3 via google-api-python-client.
All API calls are wrapped in asyncio.to_thread — never blocks the event loop.

Conflict confirmation state machine:
  When a conflict is found, _handle_add stores a PendingCalendarAdd on
  session.pending_calendar_add and returns CONFLICT_MSG. ChatService checks
  this field on the NEXT message, before intent classification, and calls
  execute_pending_add() if the user confirmed. This avoids the problem of
  "yes" being classified as 'chat' intent instead of 'calendar_add'.
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import dateparser
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

from app.services.google_auth.flow import get_credentials_for_user, get_auth_url
from app.services.google_auth.token_store import delete_calendar_tokens
from app.services.skills.registry import ParsedIntent, Skill, register

logger = logging.getLogger(__name__)

# Response templates (per CONTEXT.md locked decisions)
NOT_CONNECTED_MSG = "To use calendar features, connect your Google Calendar: {url}"
CALENDAR_ERROR_MSG = "Couldn't connect to Google Calendar. Check your account settings."
REVOKED_MSG = "Your Google Calendar access was revoked. Reconnect here: {url}"
MISSING_TITLE_MSG = "What should I call this meeting?"
MISSING_TIME_MSG = "When should I schedule that?"
CONFLICT_MSG = "You already have '{title}' at that time. Add anyway? Reply 'yes' to confirm."
NO_EVENTS_MSG = "Nothing on your calendar for the next 7 days."


@dataclass
class PendingCalendarAdd:
    """Stores the resolved event details while waiting for conflict confirmation.

    Stored on SessionState.pending_calendar_add. ChatService reads this on the
    next message, before intent classification, and calls execute_pending_add()
    if the user confirms with 'yes' / 'oui' / etc.
    """

    user_id: str
    title: str
    start_dt: datetime
    end_dt: datetime
    user_tz: str


async def execute_pending_add(pending: "PendingCalendarAdd") -> str:
    """Create the calendar event from a confirmed PendingCalendarAdd.

    Called by ChatService after the user confirms a conflict warning.
    Returns the confirmation string or an error message.
    """
    service, error = await _get_service(pending.user_id)
    if error:
        return error

    try:
        await _create_event(service, pending.title, pending.start_dt, pending.end_dt, pending.user_tz)
    except Exception as e:
        logger.error(f"Event creation failed (pending confirm) for {pending.user_id}: {e}")
        return CALENDAR_ERROR_MSG

    time_part = pending.start_dt.strftime("%-I:%M%p").lower()
    day_part = pending.start_dt.strftime("%a")
    return f"Added: {pending.title} · {day_part} · {time_part}"


def _format_event_time(event: dict) -> str:
    """Format event start time as 'Mon 3:00pm'."""
    start = event.get("start", {})
    dt_str = start.get("dateTime") or start.get("date")
    if not dt_str:
        return "?"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%a %-I:%M%p").lower().replace(":00", "")
    except ValueError:
        return dt_str[:10]


def _parse_user_date(date_string: str, user_tz: str) -> datetime | None:
    """Parse multilingual date string into aware datetime using dateparser.

    Languages: FR + EN. PREFER_DATES_FROM=future so 'Tuesday' means next Tuesday.
    Returns None if unparseable — caller should ask for clarification.
    """
    return dateparser.parse(
        date_string,
        languages=["fr", "en"],
        settings={
            "TIMEZONE": user_tz,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
            "PREFER_DAY_OF_MONTH": "first",  # "next month" -> 1st of next month
        },
    )


async def _get_service(user_id: str):
    """Load credentials and build Calendar service. Returns (service, error_message).

    Returns (None, error_msg) if not connected or tokens revoked.
    """
    try:
        creds = await get_credentials_for_user(user_id)
    except RefreshError:
        await delete_calendar_tokens(user_id)
        url = get_auth_url()
        return None, REVOKED_MSG.format(url=url)

    if creds is None:
        url = get_auth_url()
        return None, NOT_CONNECTED_MSG.format(url=url)

    try:
        service = await asyncio.to_thread(build, "calendar", "v3", credentials=creds)
        return service, None
    except Exception as e:
        logger.error(f"Failed to build Calendar service for {user_id}: {e}")
        return None, CALENDAR_ERROR_MSG


async def _check_conflicts(service, start_dt: datetime, end_dt: datetime) -> list[dict]:
    """Return events overlapping [start_dt, end_dt) on the primary calendar."""
    def _query():
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_dt.isoformat(),
                timeMax=end_dt.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        logger.error(f"Conflict check failed: {e}")
        return []


async def _create_event(service, title: str, start_dt: datetime, end_dt: datetime, user_tz: str) -> dict:
    """Create a calendar event. Runs synchronous insert in thread pool."""
    event_body = {
        "summary": title,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": user_tz},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": user_tz},
    }

    def _insert():
        return service.events().insert(calendarId="primary", body=event_body).execute()

    return await asyncio.to_thread(_insert)


async def _list_events(service, max_results: int = 10) -> list[dict]:
    """List upcoming events from now + 7 days."""
    now = datetime.now(timezone.utc)
    week_out = now + timedelta(days=7)

    def _query():
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=week_out.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])

    return await asyncio.to_thread(_query)


class CalendarSkill:
    """Handles calendar_add and calendar_view intents.

    Implements Skill Protocol: handle(user_id, intent, user_tz) -> str

    Conflict confirmation:
        When a conflict is detected, this skill stores a PendingCalendarAdd on
        session.pending_calendar_add and returns CONFLICT_MSG. The confirmation
        handling lives in ChatService (chat.py) where it can intercept the next
        message before intent classification — so 'yes' is caught as a
        confirmation, not misrouted as 'chat' intent.

        CalendarSkill.handle() signature does not receive session directly to
        keep the Skill Protocol clean. Instead, the caller (ChatService) passes
        session into handle() via a keyword argument when in conflict resolution
        mode, OR handle() accepts session as an optional parameter.

        To keep the Skill Protocol interface stable, use an alternative approach:
        CalendarSkill._handle_add() accepts session as a required parameter
        (ChatService already has session in scope and passes it through). The
        public handle() interface gains an optional `session` kwarg.
    """

    async def handle(self, user_id: str, intent: ParsedIntent, user_tz: str, session=None) -> str:
        """Route to the appropriate handler.

        session: SessionState instance passed by ChatService. Required for
                 conflict detection (to set pending_calendar_add). If None,
                 conflict is detected but confirmation path is unavailable —
                 fall back to logging a warning and returning CONFLICT_MSG anyway
                 (the state just won't be stored; Plan 05 ensures session is always passed).
        """
        if intent.skill == "calendar_add":
            return await self._handle_add(user_id, intent, user_tz, session)
        elif intent.skill == "calendar_view":
            return await self._handle_view(user_id, user_tz)
        else:
            return CALENDAR_ERROR_MSG

    async def _handle_add(self, user_id: str, intent: ParsedIntent, user_tz: str, session=None) -> str:
        """Add a meeting to Google Calendar (SECR-01).

        On conflict: stores PendingCalendarAdd on session.pending_calendar_add
        and returns CONFLICT_MSG. ChatService intercepts the next user message
        before intent classification, checks for confirmation, and calls
        execute_pending_add() if confirmed.
        """
        # --- Missing field checks (ask for single missing piece) ---
        if not intent.extracted_title:
            return MISSING_TITLE_MSG
        if not intent.extracted_date:
            return MISSING_TIME_MSG

        # --- Parse date ---
        start_dt = _parse_user_date(intent.extracted_date, user_tz)
        if start_dt is None:
            return MISSING_TIME_MSG

        # Default event duration: 1 hour
        end_dt = start_dt + timedelta(hours=1)

        # --- Load Calendar service ---
        service, error = await _get_service(user_id)
        if error:
            return error

        # --- Conflict detection ---
        try:
            conflicts = await _check_conflicts(service, start_dt, end_dt)
            if conflicts:
                conflicting_title = conflicts[0].get("summary", "another event")
                # Store pending add in session for confirmation on next message.
                # ChatService (Plan 05) checks pending_calendar_add BEFORE intent
                # classification so 'yes' is caught as confirmation, not misrouted.
                if session is not None:
                    session.pending_calendar_add = PendingCalendarAdd(
                        user_id=user_id,
                        title=intent.extracted_title,
                        start_dt=start_dt,
                        end_dt=end_dt,
                        user_tz=user_tz,
                    )
                else:
                    logger.warning(
                        f"Conflict detected for {user_id} but session not passed to handle() — "
                        "confirmation path unavailable. Ensure Plan 05 passes session to skill.handle()."
                    )
                return CONFLICT_MSG.format(title=conflicting_title)
        except Exception as e:
            logger.error(f"Conflict check error for {user_id}: {e}")
            # Non-fatal — proceed to create without conflict check

        # --- Create event ---
        try:
            await _create_event(service, intent.extracted_title, start_dt, end_dt, user_tz)
        except Exception as e:
            logger.error(f"Event creation failed for {user_id}: {e}")
            return CALENDAR_ERROR_MSG

        # --- Confirmation reply (CONTEXT.md format) ---
        time_part = start_dt.strftime("%-I:%M%p").lower()
        day_part = start_dt.strftime("%a")
        return f"Added: {intent.extracted_title} · {day_part} · {time_part}"

    async def _handle_view(self, user_id: str, user_tz: str) -> str:
        """List upcoming events (SECR-02)."""
        service, error = await _get_service(user_id)
        if error:
            return error

        try:
            events = await _list_events(service)
        except Exception as e:
            logger.error(f"Event listing failed for {user_id}: {e}")
            return CALENDAR_ERROR_MSG

        if not events:
            return NO_EVENTS_MSG

        lines = []
        for event in events:
            title = event.get("summary", "Untitled")
            time_str = _format_event_time(event)
            lines.append(f"• {time_str} — {title}")

        return "\n".join(lines)


# Register the skill at import time — importing this module adds it to the registry
_calendar_skill = CalendarSkill()
register("calendar_add", _calendar_skill)
register("calendar_view", _calendar_skill)
