from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class PhoneLinkRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_e164(cls, v: str) -> str:
        """E.164 format: + followed by 7-15 digits."""
        if not v.startswith("+") or not v[1:].isdigit() or not (7 <= len(v[1:]) <= 15):
            raise ValueError(
                "Phone must be in E.164 format: +1234567890 (+ followed by 7-15 digits)"
            )
        return v


class PreferencesResponse(BaseModel):
    id: str
    user_id: str
    whatsapp_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
