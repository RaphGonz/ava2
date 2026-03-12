---
phase: 08-infrastructure-deployment
plan: 03
subsystem: infra
tags: [hetzner, caddy, docker, ufw, letsencrypt, tls, whatsapp, production]

# Dependency graph
requires:
  - phase: 08-01
    provides: Caddyfile, docker-compose.yml, deploy.sh, nginx replaced with Caddy
  - phase: 08-02
    provides: Resend DNS records submitted, Supabase Site URL updated to production domain
provides:
  - Live production VPS (Hetzner CX32, Ubuntu 24.04) accessible at https://avasecret.org
  - Valid TLS certificate via Caddy/Let's Encrypt (automatic, no Certbot needed)
  - All 4 Docker services running: caddy, backend, worker, redis
  - UFW firewall hardened: only 22/80/443 allowed inbound
  - WhatsApp webhook verified and subscribed at https://avasecret.org/webhook
  - Production .env deployed on server with all API credentials
affects: [08-04, 09-google-oauth, 10-landing-page, 13-smoke-test]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Caddy automatic HTTPS: named volumes caddy_data/caddy_config hold TLS certs — must never be deleted"
    - "UFW allow-before-enable: SSH port 22 allowed before ufw enable to prevent lockout"
    - "deploy.sh: validates Caddyfile before restarting containers — zero-downtime config change guard"

key-files:
  created:
    - "/opt/ava2/backend/.env (on VPS) — all production credentials"
    - "/opt/ava2/frontend/.env.production (on VPS) — Supabase keys for frontend build"
  modified:
    - "/opt/ava2/Caddyfile (on VPS) — domain updated to avasecret.org"

key-decisions:
  - "CX32 chosen over CX22 — CX22 has OOM risk during ComfyUI image generation bursts (4 vCPU, 8 GB RAM)"
  - "FRONTEND_URL set to https://avasecret.org in backend/.env — prevents CORS block on all production API responses"
  - "UFW allows 443/udp in addition to 443/tcp — enables HTTP/3 (QUIC) support via Caddy"

patterns-established:
  - "Production deploy: git clone /opt/ava2 → edit Caddyfile + .env → ./deploy.sh"
  - "Firewall order: ufw allow 22 first, then 80/443, then ufw enable — prevents SSH lockout"

requirements-completed: [INFRA-01, INFRA-02, INFRA-03]

# Metrics
duration: human-action (deployment performed by user)
completed: 2026-03-05
---

# Phase 8 Plan 03: VPS Provisioning and Go-Live Summary

**Hetzner CX32 production server live at https://avasecret.org with Caddy TLS, 4 Docker services running, UFW firewall hardened, and WhatsApp webhook verified**

## Performance

- **Duration:** human-action (user-performed deployment)
- **Started:** 2026-03-05
- **Completed:** 2026-03-05
- **Tasks:** 1 (checkpoint:human-action — all 10 steps user-executed)
- **Files modified:** 0 (VPS-side only; no repo source changes)

## Accomplishments

- Hetzner CX32 VPS provisioned (Ubuntu 24.04, 4 vCPU, 8 GB RAM) — CX32 chosen to avoid OOM during ComfyUI image generation bursts
- Domain A record pointed at VPS IP; https://avasecret.org loads in browser with valid TLS cert (no warnings)
- Repository cloned to /opt/ava2; Caddyfile updated with real domain; backend/.env and frontend/.env.production created with all production credentials
- deploy.sh run successfully — all 4 services (caddy, backend, worker, redis) confirmed running via docker compose ps
- UFW firewall enabled: ports 22/80/443 allowed inbound, default deny incoming; fail2ban enabled for SSH protection
- WhatsApp webhook verified at https://avasecret.org/webhook and subscribed to messages field in Meta Developer Console

## Task Commits

This plan was a `checkpoint:human-action` — all steps were performed manually by the user on the VPS. No code changes were committed to the repository.

**Plan metadata:** (docs commit — this summary file)

## Files Created/Modified

- `/opt/ava2/backend/.env` (on VPS, not in repo) — all production API credentials
- `/opt/ava2/frontend/.env.production` (on VPS, not in repo) — Supabase URL + anon key for frontend build
- `/opt/ava2/Caddyfile` (edited on VPS) — domain set to avasecret.org

## Decisions Made

- CX32 over CX22: STATE.md pending todo from Phase 7 flagged CX22 OOM risk during image generation — CX32 (8 GB RAM) selected
- FRONTEND_URL in .env set to https://avasecret.org: critical to avoid CORS block on all API responses in production (RESEARCH.md Pitfall 6)
- UFW 443/udp added alongside 443/tcp: enables HTTP/3 (QUIC) support natively through Caddy

## Deviations from Plan

None - plan executed exactly as written. All 10 steps completed in order by user.

## Issues Encountered

None - deployment proceeded without errors. Caddy obtained TLS certificate within 30-60 seconds of first start.

## User Setup Required

This entire plan was user setup. All steps completed:
- VPS provisioned and accessible via SSH
- DNS A record propagated
- Repository cloned, Caddyfile and .env files configured
- deploy.sh executed successfully
- UFW firewall enabled with correct rules
- WhatsApp webhook verified and subscribed

## Next Phase Readiness

- Production server is live and fully operational
- All 4 Docker services running (caddy, backend, worker, redis)
- HTTPS working with auto-renewed TLS certificate
- WhatsApp messages will route to the live backend
- Plan 08-04: Verify all API credentials are functional end-to-end; verify email deliverability score >= 9/10 on mail-tester.com

---
*Phase: 08-infrastructure-deployment*
*Completed: 2026-03-05*
