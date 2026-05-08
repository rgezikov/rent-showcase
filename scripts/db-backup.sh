#!/usr/bin/env bash
# Daily PostgreSQL backup — runs via cron as the deploy user.
# Dumps the database from the running Postgres container, keeps 30 days of backups.
set -euo pipefail

APP_DIR="/opt/rent-showcase"
BACKUP_DIR="$APP_DIR/backups"
CONTAINER="rent-showcase-db-1"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DUMP_FILE="$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Load DB credentials from the production env file
ENV_FILE="$APP_DIR/.env.prod"
if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    set -a; source "$ENV_FILE"; set +a
fi

DB_NAME="${DB_NAME:-rent_showcase}"
DB_USER="${DB_USER:-rent_user}"

echo "[$TIMESTAMP] Starting backup of $DB_NAME"

docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$DUMP_FILE"

echo "[$TIMESTAMP] Backup written to $DUMP_FILE ($(du -h "$DUMP_FILE" | cut -f1))"

# Prune backups older than 30 days
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete
echo "[$TIMESTAMP] Pruned backups older than 30 days"
