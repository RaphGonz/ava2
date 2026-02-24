"""Intent classifier for secretary mode message routing.

Uses OpenAI structured outputs to classify user messages into one of four intents:
  - calendar_add: user wants to add/schedule/book an event
  - calendar_view: user wants to see their schedule/agenda/upcoming events
  - research: user wants to look up information or get a factual answer
  - chat: general conversation (fallback)

Secretary mode only — ChatService must NOT call this in intimate mode.
"""
import logging
from typing import Literal
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.services.skills.registry import ParsedIntent

logger = logging.getLogger(__name__)

INTENT_CLASSIFIER_PROMPT = """You are an intent classifier for a personal assistant bot.
Classify the user's message into exactly one of these intents:
- "calendar_add": user wants to add, schedule, or book a meeting/event/appointment
- "calendar_view": user wants to see their schedule, upcoming events, calendar, or agenda
- "research": user wants to look up information, get a factual answer, or learn about a topic
- "chat": general conversation, questions about the bot, or anything else

For calendar_add: also extract the event title and the date/time string exactly as the user stated.
For research: also extract the core search query.
Be bilingual — handle English and French naturally.

Examples:
- "Add dentist appointment Tuesday at 2pm" → calendar_add, title="dentist appointment", date="Tuesday at 2pm"
- "Ajoute une réunion d'équipe mardi à 15h" → calendar_add, title="réunion d'équipe", date="mardi à 15h"
- "What's on my calendar?" → calendar_view
- "Qu'est-ce que je fais aujourd'hui?" → calendar_view
- "What is quantum mechanics?" → research, query="quantum mechanics"
- "Qu'est-ce que la mécanique quantique?" → research, query="mécanique quantique"
- "How are you?" → chat"""


class IntentResult(BaseModel):
    intent: Literal["calendar_add", "calendar_view", "research", "chat"]
    extracted_date: str | None = None    # raw date string from user (e.g. "mardi à 15h")
    extracted_title: str | None = None  # event title for calendar_add
    query: str | None = None            # search query for research


async def classify_intent(
    client: AsyncOpenAI, text: str, model: str
) -> ParsedIntent:
    """Classify user message into a ParsedIntent.

    Uses OpenAI structured outputs — guaranteed valid enum, no JSON parsing errors.
    Falls back to 'chat' intent on any error so the message is always handled.
    """
    try:
        response = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": INTENT_CLASSIFIER_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format=IntentResult,
        )
        result = response.choices[0].message.parsed
        return ParsedIntent(
            skill=result.intent,
            raw_text=text,
            extracted_date=result.extracted_date,
            extracted_title=result.extracted_title,
            query=result.query,
        )
    except Exception as e:
        logger.error(f"Intent classification failed, defaulting to chat: {e}")
        return ParsedIntent(skill="chat", raw_text=text)
