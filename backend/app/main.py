from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.routers import auth, avatars, dev, messages, preferences, webhook, health
from app.routers import google_oauth
from app.routers import web_chat, photo
from app.config import settings

app = FastAPI(
    title="Ava API",
    description="AI companion backend — Phase 2: Infrastructure & User Management",
    version="0.1.0",
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

# Serve templates directory for minimal Phase 2 test UI
# Phase 6 will replace this with the full styled web app
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
if os.path.isdir(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
