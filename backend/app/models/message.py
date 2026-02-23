from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class MessageChannel(str, Enum):
    app = "app"
    whatsapp = "whatsapp"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class MessageCreate(BaseModel):
    user_id: str
    avatar_id: Optional[str] = None
    channel: MessageChannel
    role: MessageRole
    content: str


class MessageResponse(BaseModel):
    id: str
    user_id: str
    avatar_id: Optional[str]
    channel: MessageChannel
    role: MessageRole
    content: str
    created_at: datetime
