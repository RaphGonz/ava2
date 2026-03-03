---
phase: 08-infrastructure-deployment
plan: "01"
subsystem: infrastructure
tags: [caddy, docker, deployment, email, database]
dependency_graph:
  requires: []
  provides: [caddy-reverse-proxy, deploy-script, resend-config, usage-events-table]
  affects: [backend-config, database-schema]
tech_stack:
  added: [caddy:2.11-alpine]
  patterns: [docker-named-volumes-for-tls, spa-fallback-routing, named-api-matcher]
key_files:
  created:
    - Caddyfile
    - deploy.sh
    - backend/migrations/005_usage_events.sql
  modified:
    - docker-compose.yml
    - backend/app/config.py
decisions:
  - "Caddy named volumes (caddy_data, caddy_config) must never be deleted — they hold TLS certificates issued by Let's Encrypt"
  - "Caddyfile uses @api named matcher covering all backend path prefixes; all other paths fall through to SPA file_server"
  - "deploy.sh validates Caddyfile via Docker before restarting containers — catches config errors before downtime"
  - "resend_api_key and resend_from_address default to empty string — consistent with all other credential fields in Settings"
  - "usage_events RLS enabled with no user SELECT policy — admin reads via service role key only"
metrics:
  duration_minutes: 9
  completed_date: "2026-03-03"
  tasks_completed: 2
  files_changed: 5
---

# Phase 8 Plan 01: Caddy Infrastructure & Deployment Prep Summary

**One-liner:** Caddy reverse proxy replacing nginx in docker-compose, Caddyfile with API routing + SPA fallback, deploy.sh for repeatable VPS deploys, Resend config fields, and usage_events DB migration.

## What Was Built

### Task 1: docker-compose.yml rewrite + Caddyfile (commit: 6b9a990)

Replaced the nginx:alpine service in docker-compose.yml with caddy:2.11-alpine. The new Caddy service:
- Exposes ports 80, 443, and 443/udp (HTTP/3 QUIC)
- Mounts Caddyfile read-only from repo root
- Mounts ./frontend/dist as /srv (SPA static files)
- Uses caddy_data and caddy_config named volumes for TLS certificate persistence

The Caddyfile routes API traffic via @api named matcher covering all backend path prefixes (/auth/*, /chat/*, /billing/*, /avatars/*, /preferences/*, /photos/*, /webhook/*, /messages/*, /dev/*, /health*) to backend:8000 using the Docker service name (not localhost). All other paths fall through to file_server with try_files /index.html SPA fallback.

### Task 2: deploy.sh + config.py + migration (commit: c0113d4)

Created deploy.sh with a 4-step deployment flow:
1. Build frontend (npm ci + npm run build)
2. Validate Caddyfile via Docker (catches config errors before downtime)
3. Pull latest images and restart via docker compose up -d --build
4. Health check: docker compose ps + tail logs

Added two new fields to backend/app/config.py Settings class between sentry_dsn and redis_url:
- `resend_api_key: str = ""` — Resend Dashboard API key
- `resend_from_address: str = ""` — From address (e.g., "Ava <ava@yourdomain.com>")

Created backend/migrations/005_usage_events.sql with:
- usage_events table (id UUID, user_id UUID FK, event_type TEXT, metadata JSONB, created_at TIMESTAMPTZ)
- IF NOT EXISTS guards (idempotent, safe to re-run)
- Two composite indexes for admin dashboard queries (event_type+time, user_id+time)
- RLS enabled, no user SELECT policy (admin reads via service role only)

## Decisions Made

1. **caddy_data volume**: Named volume (not bind mount) — Caddy manages its own TLS certificate renewal; bind mount would require manual cert path management.

2. **backend:8000 not localhost:8000**: In Docker networks, `localhost` resolves to the Caddy container itself. Using the service name `backend:8000` resolves correctly via Docker DNS.

3. **deploy.sh validates Caddyfile before restart**: Avoids bringing down running containers when Caddyfile has a syntax error.

4. **empty-string defaults for Resend fields**: Consistent with all other credential fields in Settings (openai_api_key, stripe_secret_key, etc.) — missing key returns a graceful error at call time, not a startup crash.

5. **usage_events admin-only via service role**: No user SELECT RLS policy. Admin dashboard in Phase 12 reads via service role key. Regular users cannot query their own events.

## Deviations from Plan

None - plan executed exactly as written.

## Success Criteria Check

- [x] docker-compose.yml: nginx replaced by caddy:2.11-alpine with caddy_data + caddy_config volumes and 80/443/443-udp ports
- [x] Caddyfile: @api matcher covers all backend routes, SPA fallback serves index.html for unknown paths
- [x] deploy.sh: builds frontend, validates Caddyfile via Docker, restarts via docker compose up -d --build
- [x] config.py: resend_api_key and resend_from_address fields present with empty-string defaults
- [x] 005_usage_events.sql: table created with IF NOT EXISTS guard, RLS enabled, two indexes

## Self-Check: PASSED

All files verified present on disk:
- docker-compose.yml: FOUND
- Caddyfile: FOUND
- deploy.sh: FOUND
- backend/app/config.py: FOUND
- backend/migrations/005_usage_events.sql: FOUND

All commits verified in git history:
- 6b9a990 (Task 1 — Caddy + Caddyfile): FOUND
- c0113d4 (Task 2 — deploy.sh + config + migration): FOUND
