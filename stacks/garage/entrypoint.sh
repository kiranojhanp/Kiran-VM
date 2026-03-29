#!/bin/sh
# Generate garage.toml from template if not exists or template changed
CONFIG_FILE="/config/garage.toml"
TEMPLATE_FILE="/config/garage.toml.template"
TEMPLATE_HASH=$(sha256sum "$TEMPLATE_FILE" 2>/dev/null | cut -d' ' -f1)
HASH_FILE="/config/.template_hash"

if [ ! -f "$CONFIG_FILE" ] || [ "$(cat "$HASH_FILE" 2>/dev/null)" != "$TEMPLATE_HASH" ]; then
    sed -e "s|\${GARAGE_RPC_SECRET}|${GARAGE_RPC_SECRET}|g" \
        -e "s|\${GARAGE_ADMIN_TOKEN}|${GARAGE_ADMIN_TOKEN}|g" \
        -e "s|\${GARAGE_METRICS_TOKEN}|${GARAGE_METRICS_TOKEN}|g" \
        -e "s|\${GARAGE_S3_REGION}|${GARAGE_S3_REGION}|g" \
        -e "s|\${GARAGE_DOMAIN}|${GARAGE_DOMAIN}|g" \
        "$TEMPLATE_FILE" > "$CONFIG_FILE"
    echo "$TEMPLATE_HASH" > "$HASH_FILE"
fi

exec /garage -c "$CONFIG_FILE" "$@"
