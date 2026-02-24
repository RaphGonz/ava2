"""
Web platform adapter — satisfies PlatformAdapter Protocol for HTTP-originated messages.

receive() is called directly by the web_chat.py router (POST /chat).
send() is a no-op for the web adapter: the reply is returned synchronously via
the HTTP response — there is no async push needed.
"""
import logging
from app.adapters.base import NormalizedMessage
from app.services.user_lookup import get_avatar_for_user
from app.services.platform_router import route

logger = logging.getLogger(__name__)


class WebAdapter:
    """
    Concrete Web adapter. HTTP request -> ChatService -> HTTP response.
    send() is intentionally a no-op: web replies are returned in the HTTP response body.
    """

    def __init__(self, chat_service):
        self._chat_service = chat_service

    async def receive(self, message: NormalizedMessage) -> str:
        """Route inbound web message through platform_router -> ChatService."""
        avatar = await get_avatar_for_user(message.user_id)
        return await route(
            chat_service=self._chat_service,
            user_id=message.user_id,
            incoming_platform="web",
            message=message,
            avatar=avatar,
        )

    async def send(self, user_id: str, text: str) -> None:
        """No-op: web replies are returned synchronously in the HTTP response."""
        pass
