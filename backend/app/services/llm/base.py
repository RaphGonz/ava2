from typing import Protocol, runtime_checkable

# Canonical message format for OpenAI-compatible APIs
Message = dict  # {"role": "user"|"assistant"|"system", "content": str}


@runtime_checkable
class LLMProvider(Protocol):
    """
    Structural interface for LLM providers (ARCH-02: swappable without rewriting call sites).

    Any class with an async complete() method satisfies this Protocol — no inheritance needed.
    To add a new provider: implement a class with this signature, set llm_provider in config.
    """

    async def complete(
        self,
        messages: list[Message],
        system_prompt: str,
    ) -> str:
        """
        Send conversation history + system prompt, return the assistant's reply text.

        Args:
            messages: Ordered conversation history (user/assistant turns only, no system).
            system_prompt: Full system prompt prepended before messages.
        Returns:
            Assistant reply as a plain string.
        """
        ...
