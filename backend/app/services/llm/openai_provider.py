from openai import AsyncOpenAI
from app.services.llm.base import LLMProvider, Message
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """
    Concrete LLMProvider backed by OpenAI chat completions API.

    Uses AsyncOpenAI (non-blocking) — required for FastAPI/uvicorn async context.
    max_retries=1 delegates retry logic to the SDK (handles transient errors, rate limits).
    Do NOT use the synchronous OpenAI() client — it blocks the event loop.
    """

    def __init__(self, api_key: str, model: str = "gpt-4.1-mini"):
        self._client = AsyncOpenAI(api_key=api_key, max_retries=1)
        self._model = model

    async def complete(self, messages: list[Message], system_prompt: str) -> str:
        """Call OpenAI chat completions. Returns assistant reply text."""
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=full_messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            return "I'm having trouble thinking right now — try again in a moment."
