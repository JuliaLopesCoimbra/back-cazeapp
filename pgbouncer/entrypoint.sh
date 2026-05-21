#!/bin/sh
set -e

CONFIG=/etc/pgbouncer/pgbouncer.ini

envsubst < /etc/pgbouncer/pgbouncer.ini.template > "$CONFIG"

echo "[pgbouncer] configuração gerada em $CONFIG"
exec pgbouncer "$CONFIG"
