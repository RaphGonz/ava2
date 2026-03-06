#!/bin/bash
# deploy.sh — run on VPS after git pull
# Usage: ./deploy.sh
# Requires: Node 20+, Docker, Docker Compose v2
# NOTE: Run `chmod +x deploy.sh` on the server to make this script executable before first use.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== [1/4] Building frontend ==="
cd "$SCRIPT_DIR/frontend"
npm ci --silent
npm run build
echo "Frontend built successfully."

echo "=== [2/4] Validating Caddyfile ==="
cd "$SCRIPT_DIR"
docker run --rm -v "$SCRIPT_DIR:/srv" caddy:2.11-alpine caddy validate --config /srv/Caddyfile --adapter caddyfile
echo "Caddyfile is valid."

echo "=== [3/4] Restarting services ==="
cd "$SCRIPT_DIR"
docker compose pull --quiet
docker compose up -d --build --force-recreate
echo "Services restarted."

echo "=== [4/4] Checking service health ==="
sleep 5
docker compose ps
docker compose logs --tail=30 caddy backend
echo "=== Deploy complete ==="
