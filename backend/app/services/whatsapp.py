import httpx
from app.config import settings


async def send_whatsapp_message(phone_number_id: str, to: str, text: str) -> None:
    """
    Send a text message via Meta Cloud API.

    Args:
        phone_number_id: The WhatsApp Business phone number ID (from Meta dashboard)
        to: Recipient phone number in E.164 format (+1234567890)
        text: Message body text
    """
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
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
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()


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
