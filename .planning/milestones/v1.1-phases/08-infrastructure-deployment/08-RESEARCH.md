# Phase 8: Infrastructure & Deployment - Research

**Researched:** 2026-03-03
**Domain:** VPS provisioning, Caddy reverse proxy, Docker Compose, UFW firewall, Resend email DNS
**Confidence:** HIGH (Caddy, UFW), MEDIUM (Resend DNS record values, usage_events schema)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | App deployed to production VPS (Hetzner/DigitalOcean) and running | VPS provisioning + Docker Compose + SSH key setup patterns documented |
| INFRA-02 | All traffic served over HTTPS with automatic certificate renewal (Caddy) | Caddy 2.11 automatic HTTPS, caddy_data volume for cert persistence documented |
| INFRA-03 | Firewall configured — only ports 80 and 443 exposed publicly | UFW `deny` all + `allow` 22/80/443 pattern + Hetzner Cloud firewall panel documented |
| INFRA-04 | All production API credentials wired and verified (WhatsApp, ComfyUI Cloud, Stripe, OpenAI, Tavily, Supabase) | Existing `config.py` Settings class already accepts all required env vars; health-check pattern documented |
| EMAI-01 | Email DNS records (SPF/DKIM/DMARC) configured on sending domain for inbox deliverability | Resend domain verification flow + SPF/DKIM/DMARC record types documented; mail-tester.com validation approach identified |
</phase_requirements>

---

## Summary

Phase 8 is a pure infrastructure and operations phase. The application code is essentially complete from v1.0 — this phase is about getting it running on a real server behind a real domain with HTTPS, a locked-down firewall, all API keys wired in, and email DNS configured so future email features (Phase 9) work reliably.

The single most impactful decision already made is to replace nginx with **Caddy** as the reverse proxy. This eliminates the entire certbot/Let's Encrypt bootstrap ceremony. With Caddy, automatic HTTPS is a default behavior: point a domain's A record at the server, write a Caddyfile with the domain name, and Caddy obtains and auto-renews TLS certificates via ACME (Let's Encrypt by default). The `docker-compose.yml` already exists but uses nginx; it needs to be rewritten to swap nginx/certbot for Caddy with proper `caddy_data` and `caddy_config` named volumes.

**Email DNS is a hard dependency for Phase 9.** SPF, DKIM, and DMARC records propagate over 24-48 hours. They must be configured in Phase 8 — even if no email is sent yet — so Phase 9 can immediately use Resend without a waiting period. The `usage_events` table (ADMN-02) also needs to be created as a migration in this phase, since the STATE.md decision is to wire emission points as code paths are touched starting in Phase 8.

**Primary recommendation:** Swap nginx for Caddy in docker-compose.yml first, provision the VPS, deploy, validate HTTPS + firewall, then configure Resend DNS and create the `usage_events` migration. Run mail-tester.com before declaring phase complete.

---

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Caddy | 2.11.1 (latest) | Reverse proxy + automatic HTTPS + SPA file serving | Zero-config TLS, replaces nginx + certbot; already decided in STATE.md |
| Docker | 27.x | Container runtime | Already in use throughout v1.0 |
| Docker Compose | v2 (`docker compose`) | Multi-service orchestration | Already in use; docker-compose.yml exists |
| UFW | system package | Host firewall | Standard Ubuntu firewall tool; deny-all default + allow 22/80/443 |
| Resend | Python SDK `resend` (latest) | Email sending + DNS verification | Decided in STATE.md; RESEND_API_KEY + RESEND_FROM_ADDRESS env vars |
| Ubuntu 24.04 LTS | — | OS for Hetzner VPS | LTS until 2029; standard for production; Hetzner default offering |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| fail2ban | system package | SSH brute-force protection | Install alongside UFW; protects port 22 from scanners |
| unattended-upgrades | system package | Automatic security patches | Run on all Ubuntu production servers |
| `caddy validate` | built into caddy | Pre-deploy Caddyfile syntax check | Run before `docker compose up` in any deploy script |
| mail-tester.com | web service | Email deliverability score | Send test email to unique address, score must be 9/10+ |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Caddy | nginx + certbot | nginx requires separate certbot cron, volume mounts for certs; more configuration; **locked out by STATE.md decision** |
| UFW | Hetzner Cloud Firewall panel | Cloud firewall is also valid — acts above OS level; recommendation: use BOTH for defense in depth |
| Resend | SendGrid, Postmark | Resend was decided; simpler DNS setup, generous free tier for v1.1 volumes |

**Installation on server:**
```bash
# Caddy comes via Docker image — no host install needed
# UFW
sudo apt update && sudo apt install -y ufw fail2ban unattended-upgrades

# Resend Python SDK (add to requirements.txt)
pip install resend
```

---

## Architecture Patterns

### Recommended Project Structure (post-Phase 8)

```
ava2/                          # repo root (what gets cloned to VPS)
├── docker-compose.yml         # REWRITTEN: caddy replaces nginx
├── Caddyfile                  # NEW: reverse proxy + SPA config
├── backend/
│   ├── Dockerfile             # EXISTS: python:3.12-slim, uvicorn 2 workers
│   ├── .env                   # PRODUCTION: all real API keys
│   ├── app/
│   └── migrations/
│       └── 005_usage_events.sql  # NEW: usage_events table (Phase 8)
├── frontend/
│   └── dist/                  # BUILD OUTPUT: mounted into Caddy container
└── certbot/                   # RETIRE: no longer needed with Caddy
```

### Pattern 1: Caddy Docker Compose Integration

**What:** Replace the `nginx` service with a `caddy` service. Mount a `Caddyfile` from the repo root, the built frontend `dist/` directory as `/srv`, and two named volumes for cert/config persistence.

**When to use:** Any time Caddy handles TLS termination in Docker.

**The Caddyfile:**
```
# Source: https://caddyserver.com/docs/caddyfile/patterns
yourdomain.com {
    # 1. API routes — proxy to FastAPI backend
    handle /auth/* /chat/* /billing/* /avatars/* /preferences/* /photos/* /webhook/* /messages/* /dev/* /health* {
        reverse_proxy backend:8000 {
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # 2. SPA fallback — serve React build, unknown paths -> index.html
    handle {
        root * /srv
        try_files {path} /index.html
        file_server
    }

    # Compress responses
    encode gzip
}
```

**NOTE on handle matching:** Caddy `handle` blocks with path matchers must list each prefix; there is no wildcard-or syntax in a single handle. Use individual path matchers or a `handle_path` pattern. The cleaner approach matching the existing nginx.conf is:

```
yourdomain.com {
    encode gzip

    @api path /auth/* /chat/* /billing/* /avatars/* /preferences/* /photos/* /webhook/* /messages/* /dev/* /health*
    handle @api {
        reverse_proxy backend:8000
    }

    handle {
        root * /srv
        try_files {path} /index.html
        file_server
    }
}
```

**HTTP -> HTTPS:** Caddy does this automatically. No explicit redirect block is required — Caddy listens on port 80, handles ACME HTTP-01 challenges, and redirects all other HTTP to HTTPS by default.

**The docker-compose.yml (rewritten):**
```yaml
# Source: https://caddyserver.com/docs/running
version: "3.9"

services:
  caddy:
    image: caddy:2.11-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"    # HTTP/3
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./frontend/dist:/srv:ro
      - caddy_data:/data      # TLS certificates — MUST persist
      - caddy_config:/config  # auto-saved config — persist for convenience
    depends_on:
      - backend

  backend:
    build: ./backend
    env_file: ./backend/.env
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

  worker:
    build: ./backend
    command: python worker_main.py
    env_file: ./backend/.env
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  caddy_data:    # Do NOT delete — contains TLS certificates
  caddy_config:
  redis_data:
```

**CRITICAL:** `caddy_data` volume stores the TLS private keys and certificates. Deleting this volume triggers immediate certificate re-issuance (within Let's Encrypt rate limits: 5 per domain per week).

### Pattern 2: UFW Firewall Hardening

**What:** OS-level firewall on the Ubuntu host that blocks all inbound traffic except SSH (22), HTTP (80), and HTTPS (443).

**When to use:** Every production Ubuntu server.

```bash
# Source: https://community.hetzner.com/tutorials/simple-firewall-management-with-ufw

# ALWAYS allow SSH first — before enabling UFW — or you lock yourself out
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 443/udp   # HTTP/3

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable
sudo ufw enable

# Verify
sudo ufw status verbose
```

Expected output after configuration:
```
Status: active
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere
80/tcp                     ALLOW IN    Anywhere
443/tcp                    ALLOW IN    Anywhere
443/udp                    ALLOW IN    Anywhere
```

**Additional hardening (recommended, not required for Phase 8 success criteria):**
- Hetzner Cloud Firewall panel: add the same rules at the network level (defense in depth)
- fail2ban SSH jail: protects port 22 from brute-force scanners
- Disable root login + password auth in `/etc/ssh/sshd_config`

### Pattern 3: Resend Domain DNS Configuration

**What:** Add DNS records to the sending domain so email providers trust and accept Resend-sent mail.

**When to use:** Before any transactional email is sent; records must propagate (24-48 hours).

The exact record values are generated by the Resend Dashboard (resend.com/domains) when you add your domain. The record types and structure are:

| Record | Type | Name/Host | Value |
|--------|------|-----------|-------|
| SPF | TXT | `send` (subdomain) | `v=spf1 include:_spf.resend.com ~all` |
| DKIM | TXT | `resend._domainkey` (or provided selector) | Public key provided by Resend dashboard |
| MX (bounce) | MX | `send` (subdomain) | `feedback-smtp.us-east-1.amazonses.com` priority 10 |
| DMARC | TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:admin@yourdomain.com` |

**Process:**
1. Go to resend.com/domains → Add Domain → enter your sending domain
2. Resend displays the exact record values for your account — copy them
3. Add records to your DNS provider (Cloudflare, Hetzner DNS, Namecheap, etc.)
4. Click "Verify" in Resend dashboard — wait for green checkmarks
5. Set DMARC policy to `p=none` initially; upgrade to `p=quarantine` after confirming delivery
6. Send a test email to your unique mail-tester.com address, confirm score ≥ 9/10

### Pattern 4: usage_events Table Migration

**What:** Create the `usage_events` table that Phase 12 (Admin Dashboard) will query, and that Phases 8-11 will emit events into as code paths are touched.

**When to use:** Run as migration 005 in Phase 8 before any code emits events.

```sql
-- Migration: 005_usage_events.sql
-- Phase 8 — creates event log for admin dashboard (ADMN-02)
CREATE TABLE IF NOT EXISTS public.usage_events (
  id         UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    UUID        REFERENCES auth.users(id) ON DELETE SET NULL,
  event_type TEXT        NOT NULL,   -- 'message_sent' | 'photo_generated' | 'mode_switch' | 'subscription_created'
  metadata   JSONB,                  -- arbitrary event payload
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for dashboard queries (event_type + time range)
CREATE INDEX IF NOT EXISTS usage_events_event_type_idx ON public.usage_events (event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS usage_events_user_id_idx ON public.usage_events (user_id, created_at DESC);

-- RLS: admin reads all; users cannot read usage_events at all (admin-only)
ALTER TABLE public.usage_events ENABLE ROW LEVEL SECURITY;
-- No SELECT policy for regular users — admin reads via service role
```

**Emission pattern (to be added to existing code paths as they're touched):**
```python
# Non-blocking event emission — same deferred import pattern as Phase 5 audit helpers
async def emit_usage_event(user_id: str, event_type: str, metadata: dict = None) -> None:
    try:
        from app.database import supabase_admin
        supabase_admin.table("usage_events").insert({
            "user_id": user_id,
            "event_type": event_type,
            "metadata": metadata or {},
        }).execute()
    except Exception:
        pass  # DB failure must never block message delivery
```

### Pattern 5: Production env File

**What:** Backend `.env` with all production credentials.

The existing `backend/app/config.py` `Settings` class already accepts all required variables. New variables needed for v1.1:

```bash
# New for v1.1 — add to backend/.env
RESEND_API_KEY=re_...
RESEND_FROM_ADDRESS=Ava <ava@yourdomain.com>
FRONTEND_URL=https://yourdomain.com
APP_ENV=production

# Existing vars that must be production values (not dev)
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_VERIFY_TOKEN=...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
COMFYUI_API_KEY=...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
REDIS_URL=redis://redis:6379

# Optional
SENTRY_DSN=https://...@sentry.io/...
```

**NOTE:** `RESEND_API_KEY` and `RESEND_FROM_ADDRESS` are **not yet in `config.py`**. They need to be added to the `Settings` class as `resend_api_key: str = ""` and `resend_from_address: str = ""` in Phase 8 (or Phase 9 — but adding the config fields now means `.env` won't error).

**NOTE:** `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are frontend env vars (Vite build-time). They go into the **build command** or a `frontend/.env.production` file, NOT into `backend/.env`. These are needed for Phase 9's Google OAuth PKCE flow.

### Anti-Patterns to Avoid

- **Mounting `certbot/` volumes into Caddy:** Caddy manages its own certificates. The existing `certbot/` directory at the repo root is a vestige of the nginx approach and should be left untouched (not deleted, in case rollback is needed, but not referenced in the new docker-compose.yml).
- **Exposing Redis port externally:** The existing docker-compose.yml correctly does not expose Redis; keep it that way. Redis should only be reachable from within the Docker network.
- **Using `caddy:latest`:** Pin to `caddy:2.11-alpine` to prevent unexpected behavior from a future major version upgrade.
- **Deleting `caddy_data` volume:** This destroys the TLS certificates and private key. A `docker volume prune` command can silently delete it. Always use `docker volume ls` and name the volume explicitly.
- **Forgetting HTTP/3 UDP port:** `443:443/udp` is optional but important; HTTP/3 (QUIC) requires UDP 443. Add it to UFW rules if included.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TLS certificate issuance and renewal | cron + certbot scripts | Caddy automatic HTTPS | Caddy handles ACME challenge, renewal 30 days before expiry, OCSP stapling — all automatic |
| HTTP → HTTPS redirect | nginx redirect config | Caddy automatic | Caddy inserts redirect on port 80 by default; no explicit config needed |
| Email deliverability | Custom SMTP server | Resend + DNS records | SPF/DKIM/DMARC alignment is complex; Resend handles the reputation layer |
| DKIM key generation | OpenSSL manual key gen | Resend dashboard | Resend generates the key pair and gives you the TXT record value |
| IP ban on failed SSH | iptables script | fail2ban | fail2ban monitors `/var/log/auth.log` and inserts UFW rules automatically |

**Key insight:** Infrastructure automation exists precisely because these tasks have a dozen failure modes each. The correct posture is to pick mature tools and configure them, not to replicate their behavior.

---

## Common Pitfalls

### Pitfall 1: UFW Enabled Before SSH Allow
**What goes wrong:** Running `ufw enable` before `ufw allow 22` locks you out of the server over SSH. You cannot reconnect remotely; recovery requires Hetzner's in-browser console.
**Why it happens:** UFW defaults deny all incoming when first enabled.
**How to avoid:** Always run `ufw allow 22/tcp` as the first UFW command. Confirm the rule is listed with `ufw status` before running `ufw enable`.
**Warning signs:** If you ran `ufw enable` without verifying SSH is allowed, immediately use the Hetzner Cloud Console "Console" tab to access the server without SSH.

### Pitfall 2: `caddy_data` Volume Not Persisted
**What goes wrong:** `docker compose down -v` or `docker volume prune` destroys the caddy_data volume. On next start, Caddy re-requests a certificate. With Let's Encrypt rate limits (5 certs per registered domain per week), rapid re-issuance can exhaust the quota.
**Why it happens:** `-v` flag on `docker compose down` removes volumes; users do it for "clean" restarts.
**How to avoid:** Never use `docker compose down -v` in production. Use `docker compose down` without `-v`. Add a comment in docker-compose.yml on the caddy_data volume definition.
**Warning signs:** Caddy logs show `certificate manager: acme: ACME error: urn:ietf:params:acme:error:rateLimited`.

### Pitfall 3: Docker Internal Networking `localhost` Confusion
**What goes wrong:** Writing `reverse_proxy localhost:8000` in Caddyfile proxies to the Caddy container itself, not to the backend container.
**Why it happens:** In Docker networks, `localhost` resolves to the current container, not the host or another container.
**How to avoid:** Always use the Docker Compose service name: `reverse_proxy backend:8000`. This is resolved by Docker's internal DNS.
**Warning signs:** Caddy returns 502 Bad Gateway; `docker compose logs caddy` shows connection refused to `127.0.0.1:8000`.

### Pitfall 4: API Credentials Silently Ignored (Empty String Default)
**What goes wrong:** All credentials in `config.py` default to empty string. If an env var is missing from `.env`, the app starts fine but fails at runtime when the first API call is made.
**Why it happens:** The graceful-degradation pattern from v1.0 (Phase 3 decision) — missing key returns fallback message, not startup crash.
**How to avoid:** After deployment, run the API health check plan explicitly — send a WhatsApp test message, trigger a ComfyUI generation, attempt a Stripe checkout — before declaring INFRA-04 complete.
**Warning signs:** Health endpoint returns `{"status": "ok"}` even when API keys are wrong — it only checks if the server is running, not if credentials are valid.

### Pitfall 5: DNS Propagation Delay for Email Records
**What goes wrong:** Resend shows DNS records as unverified for 2-48 hours after adding them. Phase 9 email features fail because DKIM isn't verified yet.
**Why it happens:** DNS TTL propagation is not instant; global propagation takes up to 48 hours.
**How to avoid:** Add Resend DNS records as the first task of Phase 8 (before even setting up the VPS). The records propagate while everything else is configured.
**Warning signs:** Resend dashboard shows orange/red "Pending" status on DNS records. Check propagation with `dig TXT resend._domainkey.yourdomain.com`.

### Pitfall 6: `FRONTEND_URL` CORS Mismatch
**What goes wrong:** `app.main.py` adds `settings.frontend_url` to the CORS allow list. If `FRONTEND_URL` is not set in production `.env`, it defaults to `http://localhost:3000`, which doesn't match the production origin. Browsers block API responses.
**Why it happens:** The default was correct for development; forgot to override for production.
**How to avoid:** Set `FRONTEND_URL=https://yourdomain.com` in `backend/.env`.
**Warning signs:** Browser DevTools shows `Access-Control-Allow-Origin` header missing or mismatched on API responses.

### Pitfall 7: Frontend Build Not Committed to Dist Before Deploying
**What goes wrong:** Caddy's `/srv` is mounted from `./frontend/dist`. If `dist/` is stale or missing, Caddy serves an old build or a 404.
**Why it happens:** `frontend/dist/` may be in `.gitignore` (not pushed to repo). On the server, the dist needs to be built.
**How to avoid:** Either (a) add a build step to the deployment script (`cd frontend && npm ci && npm run build`), or (b) commit `dist/` to the repo (less clean but simpler). Recommended: deployment script approach.
**Warning signs:** Caddy serves old version of the app or returns 404 on `/`.

---

## Code Examples

Verified patterns from official and documented sources:

### Complete Caddyfile for This Project
```
# Source: https://caddyserver.com/docs/caddyfile/patterns

yourdomain.com {
    encode gzip

    @api path /auth/* /chat/* /billing/* /avatars/* /preferences/* /photos/* /webhook/* /messages/* /dev/* /health*
    handle @api {
        reverse_proxy backend:8000 {
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    handle {
        root * /srv
        try_files {path} /index.html
        file_server
    }
}
```

### API Credential Health Check Script
```bash
#!/bin/bash
# Run from repo root after docker compose up to verify INFRA-04

BASE="https://yourdomain.com"

echo "=== Health ==="
curl -s "$BASE/health" | python3 -m json.tool

echo "=== Supabase connection ==="
# Supabase is implicitly tested by any authenticated endpoint

echo "=== WhatsApp (verify token) ==="
curl -s "$BASE/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"

echo "=== Stripe (API reachability) ==="
curl -s -H "Authorization: Bearer $STRIPE_SECRET_KEY" \
  https://api.stripe.com/v1/products?limit=1 | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'data' in d else d)"
```

### UFW Sequence (safe, ordered)
```bash
# Source: https://community.hetzner.com/tutorials/simple-firewall-management-with-ufw
sudo ufw allow 22/tcp          # SSH — MUST be first
sudo ufw allow 80/tcp          # HTTP (Caddy needs 80 for ACME challenge)
sudo ufw allow 443/tcp         # HTTPS
sudo ufw allow 443/udp         # HTTP/3 (QUIC)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable                # Only AFTER the above
sudo ufw status verbose        # Verify
```

### Resend SDK Usage (for future Phase 9 code, added now to config.py)
```python
# Source: https://resend.com/docs/send-with-python
import resend
resend.api_key = settings.resend_api_key

params: resend.Emails.SendParams = {
    "from": settings.resend_from_address,
    "to": [user_email],
    "subject": "Welcome to Ava",
    "html": "<p>Your companion is ready.</p>",
}
email = resend.Emails.send(params)
```

### Deployment Script Outline
```bash
#!/bin/bash
# deploy.sh — run on VPS after git pull

set -e

# 1. Build frontend
cd /opt/ava2/frontend
npm ci --silent
npm run build

# 2. Validate Caddyfile
docker run --rm -v /opt/ava2:/srv caddy:2.11-alpine caddy validate --config /srv/Caddyfile

# 3. Pull latest images and restart
cd /opt/ava2
docker compose pull
docker compose up -d --build

# 4. Tail logs briefly
docker compose logs --tail=50 caddy backend
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| nginx + certbot cron | Caddy automatic HTTPS | Decided in STATE.md v1.1 | No cert bootstrap, no cron jobs, simpler config |
| `docker-compose` (v1 CLI) | `docker compose` (v2 plugin) | Docker Engine 23+ | `docker-compose.yml` still works; command is `docker compose` |
| Let's Encrypt HTTP-01 only | Caddy supports HTTP-01, TLS-ALPN-01, DNS-01 | Caddy 2.x | HTTP-01 is default and sufficient for this use case |
| Caddy 2.9 | Caddy 2.11.1 (latest stable) | April 2025 / early 2026 | Includes ECH, post-quantum crypto defaults; use `caddy:2.11-alpine` |

**Deprecated/outdated in this project:**
- `nginx.conf` at repo root: replaced by `Caddyfile` — keep the file but it is no longer used
- `certbot/` directory: no longer needed; Caddy handles TLS internally
- nginx service in `docker-compose.yml`: replaced by caddy service

---

## Open Questions

1. **Domain name**
   - What we know: The project needs a real domain with A record pointing to the VPS
   - What's unclear: Which domain/registrar the operator has; this is operator-specific
   - Recommendation: Planner should include a task for "configure DNS A record" as a manual step with instructions; it cannot be automated

2. **`RESEND_API_KEY` and `RESEND_FROM_ADDRESS` not in `config.py` yet**
   - What we know: These vars are decided in STATE.md but the Settings class doesn't have them
   - What's unclear: Should they be added in Phase 8 (infrastructure) or Phase 9 (email)?
   - Recommendation: Add them to `config.py` in Phase 8 with empty-string defaults so `.env` is forward-compatible; actual email sending code goes in Phase 9

3. **`usage_events` table schema is project-specific (no external reference)**
   - What we know: ADMN-02 requires `message_sent`, `photo_generated`, `mode_switch`, `subscription_created` event types
   - What's unclear: Full JSONB metadata shape for each event type
   - Recommendation: Keep metadata as loose JSONB for now; Phase 12 will define query patterns; the schema above is sufficient for Phase 8

4. **WhatsApp webhook URL update**
   - What we know: STATE.md has a pending todo: "Register webhook URL in Meta Developer Console after starting ngrok"
   - What's unclear: The production webhook URL is now `https://yourdomain.com/webhook` — the Meta Developer Console must be updated
   - Recommendation: Include this as an INFRA-04 sub-task; it's required for WhatsApp health check to pass

5. **Hetzner Cloud Firewall vs. UFW**
   - What we know: Both are available; Hetzner's cloud firewall operates at the network level (before traffic reaches the OS)
   - What's unclear: Whether operator has already configured Hetzner Cloud firewall
   - Recommendation: Use both for defense in depth; UFW is the primary success criterion (port scan verifies OS-level); Hetzner Cloud firewall is a bonus

---

## Sources

### Primary (HIGH confidence)
- `https://caddyserver.com/docs/caddyfile/patterns` — SPA + API handle block pattern, verified
- `https://caddyserver.com/docs/automatic-https` — automatic HTTPS behavior, HTTP redirect, port 80 ACME
- `https://caddyserver.com/docs/running` — Docker Compose volume configuration (`caddy_data`, `caddy_config`)
- `https://caddyserver.com/docs/quick-starts/reverse-proxy` — reverse proxy syntax

### Secondary (MEDIUM confidence)
- `https://community.hetzner.com/tutorials/simple-firewall-management-with-ufw` — UFW commands for Hetzner production server
- `https://resend.com/docs/send-with-python` — Python SDK usage verified against official Resend docs
- `https://dmarc.wiki/resend` — Resend DNS record types (SPF/DKIM/DMARC structure); exact values come from Resend dashboard at setup time
- `https://github.com/caddyserver/caddy/releases` — Caddy 2.11.1 confirmed as latest stable

### Tertiary (LOW confidence — requires validation at deploy time)
- Resend exact SPF record value (`v=spf1 include:_spf.resend.com ~all`) — sourced from community guides, not official Resend doc; verify against dashboard-generated records
- `caddy:2.11-alpine` Docker Hub tag availability — confirm on Docker Hub before using in compose

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Caddy and UFW are well-documented; Resend Python SDK confirmed from official docs
- Architecture: HIGH — Caddyfile patterns verified from official docs; Docker Compose volume pattern confirmed
- Pitfalls: HIGH — UFW lockout and caddy_data volume deletion are documented failure modes with clear recovery paths
- Resend DNS record exact values: MEDIUM — structure confirmed, exact values only available from Resend dashboard

**Research date:** 2026-03-03
**Valid until:** 2026-06-03 (90 days — infrastructure tooling is stable; Caddy minor version may update but patterns remain valid)
