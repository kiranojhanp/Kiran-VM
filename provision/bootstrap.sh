#!/usr/bin/env bash
# bootstrap.sh — first-run provisioning for a freshly deployed VM
#
# A new VM starts with sshd on port 22. The common role moves it to port 2222.
# Run this ONCE immediately after `pulumi up`, before running site.yml.
#
# Usage:
#   ./bootstrap.sh              # uses IP from Pulumi stack output
#   ./bootstrap.sh 1.2.3.4     # override IP manually
#
# After this completes, use the normal workflow:
#   ansible-playbook site.yml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "${SCRIPT_DIR}/../infra" && pwd)"
SSH_PORT_INITIAL=$(python3 "${SCRIPT_DIR}/scripts/infra_constant.py" SSH_PORT_INITIAL)
SSH_PORT_HARDENED=$(python3 "${SCRIPT_DIR}/scripts/infra_constant.py" SSH_PORT_HARDENED)

# Resolve IP: argument takes priority, then Pulumi stack output
if [[ -n "${1:-}" ]]; then
  PUBLIC_IP="${1}"
  echo "Using provided IP: ${PUBLIC_IP}"
else
  echo "Fetching public IP from Pulumi stack..."
  PUBLIC_IP=$(pulumi stack output publicIp --cwd "${INFRA_DIR}" 2>/dev/null)
  if [[ -z "${PUBLIC_IP}" ]]; then
    echo "ERROR: Could not read publicIp from Pulumi stack. Pass IP as argument: ./bootstrap.sh <ip>" >&2
    exit 1
  fi
  echo "Resolved IP: ${PUBLIC_IP}"
fi

cd "${SCRIPT_DIR}"

echo ""
echo "Step 1/3: Waiting for SSH to be available on port ${SSH_PORT_INITIAL}..."
for i in $(seq 1 20); do
  if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes \
       -i ~/.ssh/id_ed25519 -p "${SSH_PORT_INITIAL}" "deploy@${PUBLIC_IP}" true 2>/dev/null; then
    echo "SSH ready."
    break
  fi
  echo "  Attempt ${i}/20 — retrying in 10s..."
  sleep 10
done

# Phase 1: Run common role with port 22 kept open in iptables.
# This moves sshd to 2222 without locking us out — we stay connected on 22.
echo ""
echo "Step 2/3: Running common role on port ${SSH_PORT_INITIAL} (keeping it open in iptables)..."
ansible-playbook site.yml \
  --inventory "${PUBLIC_IP}," \
  --extra-vars "ansible_port=${SSH_PORT_INITIAL} ansible_user=deploy ansible_ssh_private_key_file=~/.ssh/id_ed25519 ansible_ssh_common_args='-o StrictHostKeyChecking=accept-new' ssh_allow_port_22=true" \
  --tags common

# Phase 2: Confirm port 2222 is now reachable, then lock down port 22.
echo ""
echo "Step 3/3: Verifying port ${SSH_PORT_HARDENED} is reachable..."
for i in $(seq 1 12); do
  if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes \
       -i ~/.ssh/id_ed25519 -p "${SSH_PORT_HARDENED}" "deploy@${PUBLIC_IP}" true 2>/dev/null; then
    echo "Port ${SSH_PORT_HARDENED} confirmed. Closing port ${SSH_PORT_INITIAL}..."
    ansible-playbook site.yml \
      --inventory "${PUBLIC_IP}," \
      --extra-vars "ansible_port=${SSH_PORT_HARDENED} ansible_user=deploy ansible_ssh_private_key_file=~/.ssh/id_ed25519 ansible_ssh_common_args='-o StrictHostKeyChecking=accept-new' ssh_allow_port_22=false" \
      --tags common
    break
  fi
  if [[ "${i}" -eq 12 ]]; then
    echo "ERROR: Port ${SSH_PORT_HARDENED} unreachable after 60s. Port ${SSH_PORT_INITIAL} left open for recovery." >&2
    echo "Investigate, then manually run: ansible-playbook site.yml --tags common" >&2
    exit 1
  fi
  echo "  Attempt ${i}/12 — retrying in 5s..."
  sleep 5
done

echo ""
echo "Bootstrap complete. sshd is on port ${SSH_PORT_HARDENED}, port ${SSH_PORT_INITIAL} is closed."
echo "Next steps:"
echo "  1. Generate inventory:  ./inventory/generate.sh"
echo "  2. Run full playbook:   ansible-playbook site.yml"
