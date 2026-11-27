#!/usr/bin/env bash
# ==============================================================================
# CodeAssessment / CodeVedha - Database Backup & Disaster Recovery Utility
# Authored by: Kantam Pavan Sai Reddy (DevOps & Infrastructure Lead)
# ==============================================================================

set -euo pipefail

BACKUP_DIR="./database/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/codeassessment_backup_${TIMESTAMP}.sql"

mkdir -p "${BACKUP_DIR}"

echo "[*] Initiating CodeAssessment database backup..."
echo "[*] Target output: ${BACKUP_FILE}"

if docker ps | grep -q "codeassessment-postgres"; then
    echo "[*] Creating PostgreSQL dump from active Docker container..."
    docker exec -t codeassessment-postgres pg_dump -U codeassessment codeassessment > "${BACKUP_FILE}"
    echo "[✓] PostgreSQL backup completed successfully: $(ls -lh "${BACKUP_FILE}" | awk '{print $5}')"
elif [ -f "backend/codeassessment_v2.db" ]; then
    echo "[*] Copying local SQLite database snapshot..."
    cp "backend/codeassessment_v2.db" "${BACKUP_DIR}/codeassessment_sqlite_${TIMESTAMP}.db"
    echo "[✓] SQLite snapshot created successfully!"
else
    echo "[!] No active PostgreSQL container or SQLite file found to back up."
    exit 1
fi

# Rotate backups: keep only 5 most recent backups
echo "[*] Pruning older backups (keeping last 5)..."
find "${BACKUP_DIR}" -type f -name "codeassessment_*" | sort -r | tail -n +6 | xargs -I {} rm -- {} 2>/dev/null || true

echo "[✓] Backup and retention cycle finished."
