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

    # Image generation (Replicate)
    replicate_api_token: str = ""  # set REPLICATE_API_TOKEN in .env

    # Billing (Stripe)
    stripe_secret_key: str = ""        # Stripe Dashboard → Developers → API keys (secret)
    stripe_webhook_secret: str = ""    # Stripe Dashboard → Webhooks → signing secret
    stripe_price_id: str = ""          # Stripe Dashboard → Products → price ID (config-driven BILL-02)

    # Monitoring
    sentry_dsn: str = ""               # Sentry project DSN (empty string = disabled)

    # Redis — for BullMQ job queue (worker service)
    redis_url: str = "redis://redis:6379"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
