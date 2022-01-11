#!/bin/bash
source /app/scripts/setenv.sh
mkdir -p ${DEFAULT_EXTRA_CONF_DIR}
export CRON_SCHEDULE
cron_config

# Fix variables not interpolated
sed -i "s/'//g" /app/scripts/backups-cron
sed -i 's/\"//g' /app/scripts/backups-cron

# Setup cron job
crontab /app/scripts/backups-cron
cron -f
