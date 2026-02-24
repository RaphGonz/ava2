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
    frontend_url: str = "http://localhost:3000"

    # LLM provider configuration
    llm_provider: str = "openai"         # "openai" for Phase 3; extend for others
    llm_model: str = "gpt-4.1-mini"     # Model alias; override via LLM_MODEL env var
    openai_api_key: str = ""            # Set in .env as OPENAI_API_KEY

    # Secretary skills — Google Calendar OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # Secretary skills — Tavily research
    tavily_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
