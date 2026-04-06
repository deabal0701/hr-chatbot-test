#!/bin/bash
set -e

CONTAINER_NAME="pgvector-db"
DB_USER="postgres"
TARGET_DB="hermesdb"  # 여기는 변경하여 동이란 DB로 변경해야함.

RESTORE_FILE="$1"

if [ -z "$RESTORE_FILE" ]; then
    echo "Usage: $0 <backup_file.dump>"
    exit 1
fi

if [ ! -f "$RESTORE_FILE" ]; then
    echo "Backup file not found: $RESTORE_FILE"
    exit 1
fi

echo "======================================"
echo " RESTORE TEST STARTING"
echo " Target DB : ${TARGET_DB}"
echo " File      : ${RESTORE_FILE}"
echo "======================================"

############################################
# 1️⃣ 기존 연결 강제 종료
############################################

docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${TARGET_DB}'
AND pid <> pg_backend_pid();
"

############################################
# 2️⃣ DROP DATABASE (단독 실행)
############################################

docker exec -i ${CONTAINER_NAME} \
psql -U ${DB_USER} -d postgres \
-c "DROP DATABASE IF EXISTS ${TARGET_DB};"

############################################
# 3️⃣ CREATE DATABASE (단독 실행)
############################################

docker exec -i ${CONTAINER_NAME} \
psql -U ${DB_USER} -d postgres \
-c "CREATE DATABASE ${TARGET_DB};"

############################################
# 4️⃣ 복구
############################################

docker cp ${RESTORE_FILE} ${CONTAINER_NAME}:/tmp/restore.dump

docker exec ${CONTAINER_NAME} \
pg_restore -U ${DB_USER} \
-d ${TARGET_DB} \
/tmp/restore.dump

docker exec ${CONTAINER_NAME} rm /tmp/restore.dump

echo "======================================"
echo " RESTORE TO ${TARGET_DB} COMPLETED"
echo "======================================"

