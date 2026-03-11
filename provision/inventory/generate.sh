#!/usr/bin/env bash
# generate.sh — write provision/inventory/hosts.ini from live Pulumi stack output
#
# Usage:
#   ./inventory/generate.sh
#
# Requires: pulumi CLI authenticated to any stack
# Run this once after every `pulumi up` to keep inventory in sync.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "${SCRIPT_DIR}/../../infra" && pwd)"
HOSTS_FILE="${SCRIPT_DIR}/hosts.ini"

echo "Fetching public IP from Pulumi stack..."
STACK_NAME=$(pulumi stack --show-name --cwd "${INFRA_DIR}" 2>/dev/null || true)
SSH_PORT_HARDENED=$(python3 "${SCRIPT_DIR}/../scripts/infra_constant.py" SSH_PORT_HARDENED)
PUBLIC_IP=$(pulumi stack output publicIp --cwd "${INFRA_DIR}" 2>/dev/null)

if [[ -z "${PUBLIC_IP}" ]]; then
  echo "ERROR: Could not read publicIp from Pulumi stack. Is the stack deployed?" >&2
  exit 1
fi

cat > "${HOSTS_FILE}" <<EOF
[server]
${PUBLIC_IP} ansible_user=deploy ansible_ssh_private_key_file=~/.ssh/id_ed25519 ansible_ssh_port=${SSH_PORT_HARDENED}

[server:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30'
EOF

echo "Written: ${HOSTS_FILE}"
echo "  Host: ${PUBLIC_IP}"
echo "  Stack: ${STACK_NAME:-unknown}"
echo "  User: deploy (port ${SSH_PORT_HARDENED})"
