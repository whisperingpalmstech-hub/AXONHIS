#!/bin/bash
# AXONHIS Disaster Recovery Script
# Restores the AXONHIS database from an encrypted or unencrypted pg_dump archive

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: ./restore_db.sh <path_to_backup_file>"
    exit 1
fi

BACKUP_FILE=$1
DB_CONTAINER="axonhis_db"
DB_USER="axonhis"
DB_NAME="axonhis_db"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE not found."
    exit 1
fi

echo "Warning: This will OVERWRITE the current active database connected to the AXONHIS container."
read -p "Are you sure you want to proceed? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 1
fi

# Decrypting step would go here if file ends with .gpg
# gpg --decrypt --batch --passphrase "YOUR_SECRET_PHRASE" "$BACKUP_FILE" > /tmp/decrypted_db.dump
# TARGET_RESTORE="/tmp/decrypted_db.dump"

TARGET_RESTORE=$BACKUP_FILE

echo "Restoring from $TARGET_RESTORE..."

# Drop and Recreate the DB for clean restore, or just pg_restore. pg_restore handles cleanly if --clean requested.
# Transfer dump to inside the container to avoid pipeline buffer issues for huge files
docker cp "$TARGET_RESTORE" "$DB_CONTAINER:/tmp/restore.dump"
docker exec "$DB_CONTAINER" pg_restore -U "$DB_USER" -d "$DB_NAME" -1 -c "/tmp/restore.dump"

echo "Database restored successfully. AXONHIS is back online."

# Cleanup
# rm /tmp/decrypted_db.dump
docker exec "$DB_CONTAINER" rm /tmp/restore.dump
