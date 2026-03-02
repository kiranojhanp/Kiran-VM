#!/usr/bin/env bash
# scripts/provision.sh
#
# Glue script: runs Pulumi to get the server IP, writes Ansible inventory,
# then runs the Ansible playbook to configure the server.
#
# Two-phase inventory logic:
#   Bootstrap (first run): SSH is on port 22 as user 'ubuntu' (fresh OCI instance).
#     Detected by probing port 22 with ssh. Inventory is written with
#     ansible_user=ubuntu ansible_ssh_port=22.
#   Hardened (subsequent runs): The 'common' role has already changed the SSH
#     port to 2222 and created the 'deploy' user. Inventory is written with
#     ansible_user=deploy ansible_ssh_port=2222.
#
# Usage:
#   ./scripts/provision.sh [--stack prod] [--tags common,docker,komodo,caddy]
#
# Prerequisites:
#   - pulumi CLI installed and logged in
#   - ansible and ansible collections installed (see ansible/requirements.yml)
#   - ansible/secrets.yml created from ansible/secrets.yml.example
#   - SSH key at ~/.ssh/id_ed25519 (or set SSH_KEY env var)
#
# Optional env vars:
#   SSH_KEY=/path/to/key  — override default SSH private key
#   ANSIBLE_TAGS=role1,role2 — run only specific roles (default: all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INFRA_DIR="${REPO_ROOT}/infra"
ANSIBLE_DIR="${REPO_ROOT}/ansible"

STACK="${PULUMI_STACK:-prod}"
SSH_KEY="${SSH_KEY:-${HOME}/.ssh/id_ed25519}"
ANSIBLE_TAGS="${ANSIBLE_TAGS:-}"

# ─── helpers ──────────────────────────────────────────────────────────────────
log() { echo "[provision] $*"; }
err() { echo "[provision] ERROR: $*" >&2; exit 1; }

# ─── validate prerequisites ───────────────────────────────────────────────────
command -v pulumi   &>/dev/null || err "pulumi not found — install from https://pulumi.com"
command -v ansible  &>/dev/null || err "ansible not found — brew install ansible / pip install ansible"
command -v ansible-playbook &>/dev/null || err "ansible-playbook not found"

[[ -f "${SSH_KEY}" ]] || err "SSH key not found at ${SSH_KEY}. Set SSH_KEY env var to override."
[[ -f "${ANSIBLE_DIR}/secrets.yml" ]] || err "Missing ${ANSIBLE_DIR}/secrets.yml — copy from secrets.yml.example and fill in values."

# ─── step 1: get public IP from Pulumi ────────────────────────────────────────
log "Fetching public IP from Pulumi stack '${STACK}'..."
cd "${INFRA_DIR}"

PUBLIC_IP="$(pulumi stack output publicIp --stack "${STACK}")"
[[ -n "${PUBLIC_IP}" ]] || err "Could not get publicIp from Pulumi stack '${STACK}'. Run 'pulumi up --stack ${STACK}' first."

log "Server IP: ${PUBLIC_IP}"

# ─── step 2: write Ansible inventory ─────────────────────────────────────────
INVENTORY_FILE="${ANSIBLE_DIR}/inventory/hosts.ini"
log "Writing inventory to ${INVENTORY_FILE}..."

mkdir -p "${ANSIBLE_DIR}/inventory"

# Bootstrap detection: probe port 22 as 'ubuntu' (fresh OCI instance).
# If it succeeds we're in bootstrap mode; otherwise assume hardened mode.
if ssh -q -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
       -o BatchMode=yes -i "${SSH_KEY}" \
       -p 22 "ubuntu@${PUBLIC_IP}" true 2>/dev/null; then
  log "Bootstrap mode detected — using ubuntu@${PUBLIC_IP}:22"
  ANSIBLE_USER="ubuntu"
  ANSIBLE_PORT="22"
else
  log "Hardened mode detected — using deploy@${PUBLIC_IP}:2222"
  ANSIBLE_USER="deploy"
  ANSIBLE_PORT="2222"
fi

cat > "${INVENTORY_FILE}" <<EOF
[fewaapp]
${PUBLIC_IP} ansible_user=${ANSIBLE_USER} ansible_ssh_private_key_file=${SSH_KEY} ansible_ssh_port=${ANSIBLE_PORT}

[fewaapp:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30'
EOF

log "Inventory written."

# ─── step 3: install Ansible collections (idempotent) ────────────────────────
log "Installing Ansible collections from requirements.yml..."
cd "${ANSIBLE_DIR}"
ansible-galaxy collection install -r requirements.yml --upgrade

# ─── step 4: run Ansible playbook ────────────────────────────────────────────
log "Running Ansible playbook..."
cd "${ANSIBLE_DIR}"

PLAYBOOK_ARGS=(
  "site.yml"
  "--inventory" "${INVENTORY_FILE}"
  "--extra-vars" "@${ANSIBLE_DIR}/secrets.yml"
  "--private-key" "${SSH_KEY}"
)

# First run: port 22 (before hardening changes SSH port to 2222)
# Subsequent runs: port 2222 (set in inventory)
# The common role's sshd_config.j2 sets Port 2222 and Ansible reconnects automatically.

if [[ -n "${ANSIBLE_TAGS}" ]]; then
  PLAYBOOK_ARGS+=("--tags" "${ANSIBLE_TAGS}")
fi

ansible-playbook "${PLAYBOOK_ARGS[@]}"

log ""
log "Provisioning complete!"
log "  SSH:       ssh -p 2222 deploy@${PUBLIC_IP}"
log "  Komodo:    https://komodo.fewa.app"
log "  App:       https://fewa.app"
