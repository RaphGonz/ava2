import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v19.0"


async def send_whatsapp_message(phone_number_id: str, to: str, text: str) -> None:
    """Send a text message via Meta Cloud API.

    Raises httpx.HTTPStatusError on API errors. Callers must catch.
    Always pin to GRAPH_API_VERSION — Meta deprecates old versions.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"WhatsApp message sent to {to}: {text[:50]}")


def parse_incoming_message(body: dict) -> dict | None:
    """
    Parse a Meta webhook payload and extract message details.

    Returns a dict with sender_phone, incoming_text, phone_number_id,
    or None if the payload doesn't contain a text message.
    """
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return None

        message = value["messages"][0]
        if message.get("type") != "text":
            return None

        return {
            "sender_phone": message["from"],
            "incoming_text": message["text"]["body"],
            "phone_number_id": value["metadata"]["phone_number_id"],
        }
    except (KeyError, IndexError):
        return None
