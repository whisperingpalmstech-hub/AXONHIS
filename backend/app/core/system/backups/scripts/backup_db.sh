#!/bin/bash
# AXONHIS Production Automated Backup Script
# Schedule this via CRON for hourly/daily backups

set -e

BACKUP_DIR="/var/backups/axonhis"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="axonhis_db"
DB_USER="axonhis"
DB_NAME="axonhis_db"

mkdir -p "$BACKUP_DIR"

echo "Starting AXONHIS database backup at $DATE"

# Create a pg_dump compressed archive
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_DIR/db_backup_$DATE.dump"

# Encrypt the backup for enterprise security (Requires recipient key, simulating via basic GPG symmetric here or AES-256)
# gpg --symmetric --cipher-algo AES256 --batch --passphrase "YOUR_SECRET_PHRASE" "$BACKUP_DIR/db_backup_$DATE.dump"
# rm "$BACKUP_DIR/db_backup_$DATE.dump" # removing the unencrypted one

echo "Backup successful: db_backup_$DATE.dump"

# Keep only the last 7 days of daily backups or last 24 hours of hourly backups (example: simple prune keeping last 30 files)
ls -1t "$BACKUP_DIR"/db_backup_*.dump | tail -n +31 | xargs -r rm --

echo "Old backups pruned."
