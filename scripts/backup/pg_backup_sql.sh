#!/bin/bash
set -e

CONTAINER_NAME="pgvector-db"
DB_USER="postgres"
DB_NAME="hermesdb"
BACKUP_DIR="/home/deabal/mureum/backup"

DATE=$(date +"%Y%m%d_%H%M%S")
DB_BACKUP_FILE="${BACKUP_DIR}/hermesdb_full_${DATE}.sql"
GLOBAL_BACKUP_FILE="${BACKUP_DIR}/globals_${DATE}.sql"

mkdir -p ${BACKUP_DIR}

echo "======================================"
echo " STARTING SQL BACKUP (Docker)"
echo " Database : ${DB_NAME}"
echo "======================================"

############################################
# 1️⃣ Database SQL Backup
############################################

docker exec ${CONTAINER_NAME} \
pg_dump -U ${DB_USER} \
-d ${DB_NAME} \
--create \
--clean \
--if-exists \
> ${DB_BACKUP_FILE}

############################################
# 2️⃣ Role / Global Objects Backup
############################################

docker exec ${CONTAINER_NAME} \
pg_dumpall -U ${DB_USER} --globals-only \
> ${GLOBAL_BACKUP_FILE}

echo "======================================"
echo " BACKUP COMPLETED"
echo " DB File     : ${DB_BACKUP_FILE}"
echo " Globals File: ${GLOBAL_BACKUP_FILE}"
echo "======================================"

