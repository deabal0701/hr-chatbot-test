#!/bin/bash
set -e

# ==========================================
# FULL IDENTICAL BACKUP SCRIPT (Docker)
# - Entire Database
# - Owner + Privileges Included
# - pgvector safe
# ==========================================

CONTAINER_NAME="pgvector-db"
DB_USER="postgres"
DB_NAME="hermesdb"
BACKUP_DIR="/home/deabal/mureum/backup"

DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/hermesdb_full_${DATE}.dump"

echo "======================================"
echo " STARTING FULL IDENTICAL BACKUP"
echo " Database : ${DB_NAME}"
echo " Output   : ${BACKUP_FILE}"
echo "======================================"

mkdir -p ${BACKUP_DIR}

# 컨테이너 내부에서 dump 생성
docker exec ${CONTAINER_NAME} \
pg_dump -U ${DB_USER} \
-d ${DB_NAME} \
-Fc \
-f /tmp/full_backup.dump

# 파일 복사
docker cp ${CONTAINER_NAME}:/tmp/full_backup.dump ${BACKUP_FILE}

# 임시파일 제거
docker exec ${CONTAINER_NAME} rm /tmp/full_backup.dump

echo "======================================"
echo " BACKUP COMPLETED SUCCESSFULLY"
echo "======================================"

