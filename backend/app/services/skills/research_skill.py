"""Research skill for secretary mode.

Handles 'research' intent (SECR-03): searches Tavily and returns a concise
3-5 sentence answer with one source link.

Design:
- Tavily include_answer="advanced" returns an AI-generated answer — no extra LLM call needed
- TavilyClient.search() is synchronous — wrapped in asyncio.to_thread
- Broad/ambiguous queries (detected by low confidence signal) ask one clarifying question
- Graceful degradation: Tavily API failure → plain error message, never exception details
"""
import asyncio
import logging

from tavily import TavilyClient

from app.config import settings
from app.services.skills.registry import ParsedIntent, Skill, register

logger = logging.getLogger(__name__)

# Response templates (per CONTEXT.md locked decisions)
RESEARCH_ERROR_MSG = "Couldn't look that up right now — try again in a moment."
NO_ANSWER_MSG = "I'm not fully certain, but this topic doesn't have a clear consensus answer yet. Try rephrasing or ask for a specific aspect of it."
AMBIGUOUS_QUERY_MSG = "That's a broad topic — are you looking for a general overview, a recent development, or something specific about it?"

# Minimum answer length to use directly (avoid "I don't know" style Tavily non-answers)
MIN_ANSWER_LENGTH = 20


def _is_query_ambiguous(query: str | None) -> bool:
    """Heuristic: single-word or very short queries are likely ambiguous/broad.

    A one-word query like "physics" or "history" needs clarification.
    Full-sentence questions ("What is quantum entanglement?") are specific enough.
    Per CONTEXT.md: ask one clarifying question for broad questions.
    """
    if not query:
        return True
    words = query.strip().split()
    # Fewer than 3 words and no question word → likely ambiguous
    question_starters = {"what", "how", "why", "when", "where", "who", "which",
                         "qu", "comment", "pourquoi", "quand", "où", "qui"}
    first_word = words[0].lower().rstrip("'")
    return len(words) < 3 and first_word not in question_starters


async def _search_tavily(query: str, api_key: str) -> tuple[str, str]:
    """Run Tavily search and return (answer_text, source_url).

    Returns ("", "") on any failure — caller handles gracefully.
    TavilyClient.search() is synchronous — runs in asyncio.to_thread.
    """
    try:
        client = TavilyClient(api_key=api_key)
        response = await asyncio.to_thread(
            client.search,
            query,
            include_answer="advanced",
            max_results=3,
            search_depth="basic",
        )
        answer = response.get("answer") or ""
        results = response.get("results", [])
        source_url = results[0]["url"] if results else ""
        return answer, source_url
    except Exception as e:
        logger.error(f"Tavily search failed for query '{query}': {e}")
        return "", ""


class ResearchSkill:
    """Handles the 'research' intent (SECR-03).

    Implements Skill Protocol: handle(user_id, intent, user_tz) -> str
    """

    async def handle(self, user_id: str, intent: ParsedIntent, user_tz: str) -> str:
        """Answer a research question using Tavily search.

        Steps:
        1. Check if query is too broad — ask clarifying question if so
        2. Check Tavily API key is configured
        3. Run Tavily search in thread pool
        4. Format answer: paragraph + "Source: [url]"
        5. Graceful fallback on any failure
        """
        query = intent.query or intent.raw_text

        # Guard: ambiguous/broad query → ask for clarification (per CONTEXT.md)
        if _is_query_ambiguous(query):
            return AMBIGUOUS_QUERY_MSG

        # Guard: Tavily not configured
        if not settings.tavily_api_key:
            logger.warning("TAVILY_API_KEY not configured — research skill unavailable")
            return RESEARCH_ERROR_MSG

        # Search
        answer, source_url = await _search_tavily(query, settings.tavily_api_key)

        # Handle API failure
        if not answer and not source_url:
            return RESEARCH_ERROR_MSG

        # Handle empty or too-short answer (Tavily occasionally returns minimal text)
        if not answer or len(answer.strip()) < MIN_ANSWER_LENGTH:
            return NO_ANSWER_MSG

        # Format per CONTEXT.md: answer paragraph + one source link, nothing else
        response = answer.strip()
        if source_url:
            response = f"{response}\n\nSource: {source_url}"

        return response


# Register at import time — importing this module adds 'research' to the registry
_research_skill = ResearchSkill()
register("research", _research_skill)
