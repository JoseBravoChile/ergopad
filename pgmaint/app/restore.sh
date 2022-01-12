#!/bin/bash
echo "TARGET_DB: ${TARGET_DB}"
echo "WITH_POSTGIS: ${WITH_POSTGIS}"
echo "TARGET_ARCHIVE: ${TARGET_ARCHIVE}"

if [ -z "${TARGET_ARCHIVE:-}" ] || [ ! -f "${TARGET_ARCHIVE:-}" ]; then
	echo "TARGET_ARCHIVE needed."
	exit 1
fi

if [ -z "${TARGET_DB:-}" ]; then
	echo "TARGET_DB needed."
	exit 1
fi

echo "Dropping target DB"
PGPASSWORD=${POSTGRES_PASS} dropdb -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} --if-exists ${TARGET_DB}
PGPASSWORD=${POSTGRES_PASS} createdb -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -O ${POSTGRES_USER} ${TARGET_DB}

echo "Restoring dump file"
PGPASSWORD=${POSTGRES_PASS} pg_restore -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} ${TARGET_ARCHIVE} -d ${TARGET_DB} -j 4
