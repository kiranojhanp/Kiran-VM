#!/usr/bin/env bash
# provision-pyinfra.sh — provision the fewa.app server using pyinfra
# Usage: bash scripts/provision-pyinfra.sh
# All secrets must be set as environment variables before running.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYINFRA_DIR="$SCRIPT_DIR/../pyinfra"

# ── Check pyinfra is installed ────────────────────────────────────────────────
if ! command -v pyinfra &>/dev/null; then
  echo "pyinfra not found — installing..."
  pip install pyinfra
fi

# ── Validate required env vars ────────────────────────────────────────────────
REQUIRED_VARS=(
  DEPLOY_PASSWORD
  DEPLOY_SSH_PUBLIC_KEY
  SUDO_PASSWORD
  CLOUDFLARE_API_TOKEN
  FERRETDB_POSTGRES_PASSWORD
  KOMODO_JWT_SECRET
  KOMODO_PASSWORD
  KOMODO_PASSKEY
  KOMODO_WEBHOOK_SECRET
  SHARED_POSTGRES_PASSWORD
  SHARED_POSTGRES_SURE_PASSWORD
  SHARED_POSTGRES_GITEA_PASSWORD
  SHARED_POSTGRES_NOCODB_PASSWORD
  GITEA_SECRET_KEY
  SURE_SECRET_KEY_BASE
  OPENAI_ACCESS_TOKEN
  NOCODB_JWT_SECRET
  DATABASUS_SECRET_KEY
  R2_ACCESS_KEY_ID
  R2_SECRET_ACCESS_KEY
)

MISSING=()
for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    MISSING+=("$var")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "ERROR: Missing required environment variables:"
  for var in "${MISSING[@]}"; do
    echo "  - $var"
  done
  echo ""
  echo "Set them in your shell or source a secrets file before running."
  exit 1
fi

echo "All required env vars present."

# ── Run pyinfra ───────────────────────────────────────────────────────────────
cd "$PYINFRA_DIR"

if [[ "${1:-}" == "--dry" ]]; then
  echo "Running dry run..."
  pyinfra inventory.py deploy.py --dry
else
  echo "Provisioning server..."
  pyinfra inventory.py deploy.py
fi
