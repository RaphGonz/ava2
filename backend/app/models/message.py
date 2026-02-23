from pydantic import BaseModel
from typing import Optional
from enum import Enum


class MessageChannel(str, Enum):
    app = "app"
    whatsapp = "whatsapp"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class MessageCreate(BaseModel):
    avatar_id: Optional[str] = None
    channel: MessageChannel
    role: MessageRole
    content: str


class MessageResponse(BaseModel):
    id: str
    user_id: str
    avatar_id: Optional[str] = None
    channel: str
    role: str
    content: str
    created_at: str
