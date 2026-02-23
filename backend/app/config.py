from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase — get from Supabase Dashboard -> Settings -> API
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # WhatsApp Cloud API — get from Meta for Developers -> App -> WhatsApp -> API Setup
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""  # Any secret string you choose for webhook verification

    # App
    app_env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
