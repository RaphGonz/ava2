from pydantic import BaseModel, field_validator
from typing import Optional, Literal, Any
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
    preferred_platform: Optional[str] = "whatsapp"
    spiciness_level: Optional[str] = "mild"
    mode_switch_phrase: Optional[str] = None
    notif_prefs: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class PreferencesPatchRequest(BaseModel):
    """Partial update of user preferences — all fields optional."""
    preferred_platform: Optional[Literal["whatsapp", "web"]] = None
    spiciness_level: Optional[Literal["mild", "spicy", "explicit"]] = None
    mode_switch_phrase: Optional[str] = None   # None = use system defaults
    notif_prefs: Optional[dict[str, Any]] = None
