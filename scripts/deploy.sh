#!/usr/bin/env bash
# Run on the server as deploy user to pull latest code and rebuild the app.
# Usage: ./scripts/deploy.sh
set -euo pipefail

APP_DIR="/opt/rent-showcase"
cd "$APP_DIR"

echo "==> Pulling latest code"
git pull

echo "==> Rebuilding and restarting app"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build app

echo "==> Done. Current status:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
