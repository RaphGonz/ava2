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

    # Image generation (Replicate — legacy, unused. ComfyUI Cloud is the active provider.)
    replicate_api_token: str = ""

    # Image generation (ComfyUI Cloud — primary)
    comfyui_api_key: str = ""      # set COMFYUI_API_KEY in .env
    comfyui_base_url: str = "https://cloud.comfy.org"

    # Billing (Stripe)
    stripe_secret_key: str = ""        # Stripe Dashboard → Developers → API keys (secret)
    stripe_webhook_secret: str = ""    # Stripe Dashboard → Webhooks → signing secret
    stripe_price_id_basic: str = ""    # Stripe Dashboard → Products → Basic plan price ID (€4.99/month)
    stripe_price_id_premium: str = "" # Stripe Dashboard → Products → Premium plan price ID (€19.99/month)
    stripe_price_id_elite: str = ""   # Stripe Dashboard → Products → Elite plan price ID (€49.99/month)

    # Monitoring
    sentry_dsn: str = ""               # Sentry project DSN (empty string = disabled)

    # Email (Resend) — add RESEND_API_KEY and RESEND_FROM_ADDRESS to backend/.env
    resend_api_key: str = ""           # Resend Dashboard -> API Keys
    resend_from_address: str = ""      # e.g. "Ava <ava@yourdomain.com>"

    # Supabase auth hook — Supabase Dashboard -> Authentication -> Hooks -> Send Email -> Secret
    supabase_hook_secret: str = ""  # Format: v1,whsec_<base64>; defaults to empty (disabled)

    # Redis — for BullMQ job queue (worker service)
    redis_url: str = "redis://redis:6379"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
