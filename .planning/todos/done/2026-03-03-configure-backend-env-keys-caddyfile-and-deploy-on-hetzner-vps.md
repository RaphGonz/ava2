---
created: 2026-03-03T18:20:31.899Z
title: Configure backend .env keys, Caddyfile domain, and deploy on Hetzner VPS
area: general
files: []
---

## Problem

During phase 08-03 (VPS provisioning), the fresh Hetzner server now has Docker + docker-compose-plugin installed and the repo cloned to `/opt/ava2`. The following manual steps still need to be completed before the deploy can succeed:

1. **Write `backend/.env`** — populate all production API keys (Supabase URL + keys, OpenAI, Stripe secret + webhook secret, WhatsApp token + verify token + phone number ID, ComfyUI, Tavily, Resend API key + from address `noreply@avasecret.org`)
2. **Update Caddyfile** — replace any placeholder domain with `avasecret.org` (and optionally `www.avasecret.org`)
3. **Run `deploy.sh`** — `cd /opt/ava2 && chmod +x deploy.sh && ./deploy.sh`
4. **Verify** — `docker compose ps` shows 4 services up; `curl -I http://avasecret.org` returns 301; `https://avasecret.org` loads in browser with valid cert

## Solution

SSH into the Hetzner server (`ssh root@<VPS_IP>`), then follow steps above. The `deploy.sh` script handles frontend build, Caddyfile validation, and `docker compose up -d --build`. Caddy auto-provisions a Let's Encrypt cert on first request once the A record resolves to the VPS IP.
