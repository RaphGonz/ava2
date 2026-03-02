import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.routers import auth, avatars, dev, messages, preferences, webhook, health
from app.routers import google_oauth
from app.routers import web_chat, photo, billing
from app.config import settings

logger = logging.getLogger(__name__)

# Sentry init — call BEFORE FastAPI app creation
# Empty DSN (dev default) = disabled; production DSN in env
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.app_env,
    traces_sample_rate=0.1,  # 10% of requests for performance tracing
    # FastAPI integration activates automatically — no explicit FastApiIntegration() needed
)


def _ensure_storage_buckets() -> None:
    """
    Idempotently create Supabase Storage buckets required by the application.
    Called at startup so the buckets exist before any upload attempt.

    Buckets:
      - photos (private): reference images and generated scene photos.

    Uses service role client — only service role can create buckets.
    Silently ignores 'already exists' errors so this is safe to call on every boot.
    """
    from app.database import supabase_admin
    from storage3.exceptions import StorageApiError

    try:
        supabase_admin.storage.create_bucket("photos", options={"public": False})
        logger.info("Supabase Storage: created 'photos' bucket")
    except StorageApiError as e:
        # "The resource already exists" — bucket was already created, nothing to do
        if "already exists" in str(e).lower() or "Duplicate" in str(e):
            logger.debug("Supabase Storage: 'photos' bucket already exists — skipping creation")
        else:
            # Unexpected storage error at startup — log loudly but do not crash the app
            logger.error(f"Supabase Storage: failed to create 'photos' bucket at startup: {e}")
    except Exception as e:
        logger.error(f"Supabase Storage: unexpected error ensuring 'photos' bucket: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan: run startup tasks before yielding, teardown after.
    Replaces the deprecated @app.on_event("startup") pattern.
    """
    _ensure_storage_buckets()
    yield


app = FastAPI(
    title="Ava API",
    description="AI companion backend — Phase 2: Infrastructure & User Management",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware — allow localhost origins for development and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        settings.frontend_url,  # Add production URL from env
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dev.router)
app.include_router(avatars.router)
app.include_router(preferences.router)
app.include_router(webhook.router)
app.include_router(messages.router)
app.include_router(google_oauth.router)
app.include_router(web_chat.router)
app.include_router(photo.router)
app.include_router(billing.router)

# Serve templates directory for minimal Phase 2 test UI
# Phase 6 will replace this with the full styled web app
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
if os.path.isdir(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
