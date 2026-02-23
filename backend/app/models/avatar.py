from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum


class PersonalityType(str, Enum):
    playful = "playful"
    dominant = "dominant"
    shy = "shy"
    caring = "caring"
    intellectual = "intellectual"
    adventurous = "adventurous"


class AvatarCreate(BaseModel):
    name: str
    age: int
    personality: PersonalityType
    physical_description: Optional[str] = None

    @field_validator("age")
    @classmethod
    def age_must_be_at_least_20(cls, v: int) -> int:
        if v < 20:
            raise ValueError("Avatar age must be at least 20 (compliance requirement)")
        return v


class AvatarResponse(BaseModel):
    id: str
    user_id: str
    name: str
    age: int
    personality: str
    physical_description: Optional[str] = None
    created_at: str
