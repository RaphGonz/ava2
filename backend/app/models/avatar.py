from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PersonalityType(str, Enum):
    playful = "playful"
    dominant = "dominant"
    shy = "shy"
    caring = "caring"
    intellectual = "intellectual"
    adventurous = "adventurous"


class AvatarCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=20, description="Avatar age — minimum 20 per compliance policy")
    personality: PersonalityType
    physical_description: Optional[str] = Field(None, max_length=2000)


class AvatarResponse(BaseModel):
    id: str
    user_id: str
    name: str
    age: int
    personality: PersonalityType
    physical_description: Optional[str] = None
    created_at: datetime
