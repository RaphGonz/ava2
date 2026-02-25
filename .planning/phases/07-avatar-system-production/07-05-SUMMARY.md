---
phase: 07-avatar-system-production
plan: "05"
subsystem: billing-ui-production-deployment
tags: [stripe, billing, docker, nginx, sentry, frontend]
dependency_graph:
  requires: ["07-02"]
  provides: [subscribe-page, paywall-banner, docker-compose, nginx-config, sentry-init, env-example]
  affects: [frontend-routing, backend-startup, production-deployment]
tech_stack:
  added: [sentry-sdk, docker-compose, nginx, dockerfile]
  patterns: [stripe-checkout-redirect, paywall-402-detection, docker-multi-service, spa-nginx-proxy]
key_files:
  created:
    - frontend/src/api/billing.ts
    - frontend/src/pages/SubscribePage.tsx
    - docker-compose.yml
    - nginx.conf
    - backend/Dockerfile
  modified:
    - frontend/src/pages/ChatPage.tsx
    - frontend/src/api/chat.ts
    - backend/app/main.py
    - backend/requirements.txt
    - backend/.env.example
decisions:
  - "ApiError class added to chat.ts exposing HTTP status — enables 402 detection without query-layer changes"
  - "backend/Dockerfile created (python:3.12-slim) as Rule 3 auto-fix — docker-compose build directive requires it"
  - "useSendMessage accepts optional onError callback — keeps mutation hook composable without breaking existing callers"
metrics:
  duration_minutes: 23
  completed_date: "2026-02-25"
  tasks_completed: 2
  files_changed: 10
---

# Phase 7 Plan 05: Billing UI + Production Deployment Summary

SubscribePage with Stripe Checkout redirect, ChatPage 402 paywall banner, Docker Compose four-service production stack (nginx + backend + worker + redis), nginx reverse proxy with SPA fallback, Sentry error tracking initialization, and complete .env.example documentation.

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | SubscribePage + billing API + ChatPage paywall banner + Sentry init | `66ada3e` | billing.ts, SubscribePage.tsx, ChatPage.tsx, chat.ts, main.py, requirements.txt |
| 2 | Docker Compose production config + nginx.conf + .env.example | `b6d6b45` | docker-compose.yml, nginx.conf, .env.example, Dockerfile |

## What Was Built

### Task 1: Billing UI + Sentry

**`frontend/src/api/billing.ts`** — `createCheckoutSession(token)` calls `POST /billing/checkout` and returns `{ checkout_url }`. Throws `Error` with backend `detail` message on failure.

**`frontend/src/pages/SubscribePage.tsx`** — Full subscribe page with:
- `POST /billing/checkout` → `window.location.href = checkout_url` redirect
- Loading state: "Redirecting to checkout..."
- Cancel feedback: checks `?cancelled=1` URL param, shows yellow warning
- Error display for failed checkout session creation
- Dark UI (gray-950 background) matching app theme

**`frontend/src/pages/ChatPage.tsx`** — Added 402 paywall banner:
- `subscriptionRequired` state initialized to `false`
- `useSendMessage` now accepts `onError` callback — sets `subscriptionRequired = true` when `ApiError.status === 402`
- Yellow banner above ChatInput: "Subscription required to send messages" + "Subscribe" link to `/subscribe`

**`frontend/src/api/chat.ts`** — Added `ApiError` class (extends Error, exposes `status: number`) and `UseSendMessageOptions` interface for composable `onError` injection. Fetch now reads response body before throwing to include backend detail message.

**`backend/app/main.py`** — `sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env, traces_sample_rate=0.1)` added before `app = FastAPI()`. Empty DSN = disabled (safe for dev).

**`backend/requirements.txt`** — `sentry-sdk` added.

### Task 2: Production Deployment

**`docker-compose.yml`** — Four services:
- `nginx`: nginx:alpine, ports 80/443, mounts nginx.conf + frontend/dist + certbot/conf
- `backend`: python:3.12-slim build, uvicorn with 2 workers, reads backend/.env
- `worker`: same image, `python worker_main.py` command
- `redis`: redis:7-alpine, AOF persistence (`--appendonly yes`), internal only (no exposed port), named volume `redis_data`

**`nginx.conf`** — Regex location `~ ^/(auth|chat|billing|avatars|preferences|photos|webhook|messages|dev|health)` proxies to `backend:8000` with 120s read timeout (for image generation). `location /` serves SPA with `try_files $uri $uri/ /index.html`. Gzip enabled for text/css/js/json.

**`backend/.env.example`** — Complete documentation of all env vars:
- Supabase, OpenAI, Replicate, Stripe (SECRET_KEY + WEBHOOK_SECRET + PRICE_ID), Sentry DSN
- UptimeRobot: dashboard-only setup instructions (no env var)
- WhatsApp, Google OAuth, Tavily (all optional)
- APP_ENV, FRONTEND_URL, LLM_PROVIDER, LLM_MODEL, REDIS_URL

**`backend/Dockerfile`** — Created as Rule 3 auto-fix (blocking: docker-compose `build: ./backend` requires Dockerfile). python:3.12-slim, copies requirements.txt first for layer caching, default CMD overridden by docker-compose per service.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Missing Referenced File] Created backend/Dockerfile**
- **Found during:** Task 2
- **Issue:** `docker-compose.yml` uses `build: ./backend` for both `backend` and `worker` services, but no Dockerfile existed in `backend/` — docker-compose would fail at `docker compose up -d`
- **Fix:** Created `backend/Dockerfile` using `python:3.12-slim`, installs requirements.txt, copies app code. CMD is overridden per service in docker-compose.
- **Files modified:** `backend/Dockerfile` (created)
- **Commit:** `b6d6b45`

**2. [Rule 2 - Missing Critical Functionality] Added ApiError class + onError option to useSendMessage**
- **Found during:** Task 1
- **Issue:** Existing `useSendMessage` threw a generic `Error('Failed to send message')` for all HTTP errors. ChatPage could not distinguish 402 (subscription required) from other errors without status code.
- **Fix:** Added `ApiError` class exposing `status: number`; updated `useSendMessage` to accept `UseSendMessageOptions.onError` callback; fetch now reads response body before throwing.
- **Files modified:** `frontend/src/api/chat.ts`
- **Commit:** `66ada3e`

## Verification Results

| Check | Result |
|-------|--------|
| `npm run build` | PASS — 106 modules, 0 TS errors |
| `grep "sentry_sdk.init" backend/app/main.py` | FOUND |
| `grep "sentry-sdk" backend/requirements.txt` | FOUND |
| `grep "worker_main" docker-compose.yml` | FOUND |
| `grep "STRIPE_SECRET_KEY" backend/.env.example` | FOUND |
| `grep "REPLICATE_API_TOKEN" backend/.env.example` | FOUND |
| `grep "UptimeRobot" backend/.env.example` | FOUND |
| `grep "proxy_pass" nginx.conf` | FOUND |
| `python -m pytest tests/ -x -q` | 47 passed, 0 failures |

## Success Criteria Check

1. SubscribePage: Subscribe button → `POST /billing/checkout` → `window.location.href` to Stripe Checkout URL — DONE
2. Cancelled checkout: `/subscribe?cancelled=1` shows "Checkout cancelled — no charge made." — DONE
3. ChatPage: 402 response shows yellow paywall banner with `/subscribe` link — DONE
4. Sentry: `sentry_sdk.init(dsn=settings.sentry_dsn)` in main.py before `FastAPI()`; empty DSN = disabled — DONE
5. Docker Compose: nginx + backend + worker + redis; worker runs `python worker_main.py`; redis AOF — DONE
6. nginx.conf: proxies all API paths to backend:8000; serves SPA with try_files fallback — DONE
7. .env.example: STRIPE_SECRET_KEY, STRIPE_PRICE_ID, REPLICATE_API_TOKEN, SENTRY_DSN documented — DONE
8. .env.example: UptimeRobot dashboard-only setup instructions included — DONE

## Self-Check: PASSED
