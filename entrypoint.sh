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
  chmod 666 "$CONFIG_FILE"
fi

chmod 777 /data /config 2>/dev/null || true

exec "$@"
