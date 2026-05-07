#!/bin/sh
set -e

CONFIG_FILE="/config/config.json"
SAMPLE_FILE="/app/config.json.sample"

if [ -f "$CONFIG_FILE" ]; then
  echo "Using existing config: $CONFIG_FILE"
else
  echo "Using default config."
  mkdir -p "$(dirname "$CONFIG_FILE")"
  cp "$SAMPLE_FILE" "$CONFIG_FILE"
fi

PUID=${PUID:-0}
PGID=${PGID:-0}

if [ "$PUID" != "0" ]; then
  echo "Running as PUID=$PUID PGID=$PGID"
  chown -R "$PUID:$PGID" /config /data 2>/dev/null || true
  exec su-exec "$PUID:$PGID" "$@"
fi

# Fallback for root mode
chmod 666 "$CONFIG_FILE" 2>/dev/null || true
chmod 777 /config 2>/dev/null || true

exec "$@"
