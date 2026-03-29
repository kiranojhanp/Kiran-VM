#!/bin/sh
# Generate garage.toml from template by substituting environment variables
# envsubst requires gettext, so we use shell parameter expansion for portability
if command -v envsubst >/dev/null 2>&1; then
    envsubst < /etc/garage.toml.template > /etc/garage.toml
else
    sed -e "s|\${GARAGE_RPC_SECRET}|${GARAGE_RPC_SECRET}|g" \
        -e "s|\${GARAGE_ADMIN_TOKEN}|${GARAGE_ADMIN_TOKEN}|g" \
        -e "s|\${GARAGE_METRICS_TOKEN}|${GARAGE_METRICS_TOKEN}|g" \
        -e "s|\${GARAGE_S3_REGION}|${GARAGE_S3_REGION}|g" \
        -e "s|\${GARAGE_DOMAIN}|${GARAGE_DOMAIN}|g" \
        /etc/garage.toml.template > /etc/garage.toml
fi
exec /garage -c /etc/garage.toml "$@"
