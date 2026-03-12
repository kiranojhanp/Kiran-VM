# ansible — server provisioning

Ansible playbooks for the production server running on Oracle Cloud (ARM64 Ubuntu).

This layer handles OS hardening, Docker, shared infrastructure (Postgres + Redis), and Komodo installation. After initial provisioning, ongoing stack deploys are handled by [Komodo](https://komo.do).

## Prerequisites

```bash
pip install ansible
ansible-galaxy collection install -r requirements.yml
```

Ensure `~/.vault_pass` exists — see [Vault](#vault).

---

## First-time setup (fresh VM)

Run these steps **once** in order after `pulumi up` in `../infra`.

### 1. Generate inventory

```bash
task hosts
```

Reads the public IP from the live Pulumi stack and writes `inventory/hosts.ini`. Re-run whenever the VM is replaced.

### 2. Bootstrap (initial SSH port → hardened SSH port)

A fresh VM starts on the initial SSH port from generated `../infra/constants.py` (sourced from `../Taskfile.yml`, default `22`). The `common` role then moves sshd to the hardened port from that same generated constants file (default `2222`). Bootstrap keeps the initial port open during the transition, confirms the hardened port is reachable, and then closes the initial port.

```bash
task bootstrap
```

### 3. Full provisioning

```bash
task provision
```

Equivalent direct commands:

```bash
./inventory/generate.sh
./bootstrap.sh
ansible-playbook -i inventory/hosts.ini site.yml --extra-vars "@secrets.yml"
```

---

## Day-to-day usage

Recommended (from repo root):

```bash
task hosts
task provision
```

Direct Ansible usage (from `provision/`):

```bash
# Full playbook
ansible-playbook -i inventory/hosts.ini site.yml --extra-vars "@secrets.yml"

# Dry run — shows what would change without applying it
ansible-playbook -i inventory/hosts.ini site.yml --extra-vars "@secrets.yml" --check --diff

# Single role
ansible-playbook -i inventory/hosts.ini site.yml --extra-vars "@secrets.yml" --tags docker

# Service roles
ansible-playbook -i inventory/hosts.ini site.yml --extra-vars "@secrets.yml" --tags services

# Skip a role
ansible-playbook -i inventory/hosts.ini site.yml --extra-vars "@secrets.yml" --skip-tags infra
```

Available tags: `common`, `hardening`, `docker`, `infra`, `komodo`, `services`

`generate.sh` and `bootstrap.sh` read shared SSH ports from generated `../infra/constants.py` (from `../Taskfile.yml` vars), so Pulumi and Ansible stay aligned without duplicate hardcoded values.

`task provision` also passes `shared_docker_network` from `Taskfile.yml` (`SHARED_DOCKER_NETWORK`, default `internal-network`).

---

## Vault

Secrets are stored in `secrets.yml`, encrypted with [ansible-vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html). The vault password lives at `~/.vault_pass` (outside the repo, never committed), and `ansible.cfg` reads it automatically.

### Setup on a new machine

Get the vault password from your password manager, then:

```bash
echo 'your-vault-password' > ~/.vault_pass
chmod 600 ~/.vault_pass
```

### View / edit secrets

```bash
ansible-vault view secrets.yml
ansible-vault edit secrets.yml
```

### Rotate the vault password

```bash
ansible-vault rekey secrets.yml
# update ~/.vault_pass with the new value
```

`secrets.yml` is the source of truth for required secrets. Use `ansible-vault view secrets.yml` to inspect current keys and `ansible-vault edit secrets.yml` to add or update values.

---

## Key files

| File                       | Purpose                                              |
| -------------------------- | ---------------------------------------------------- |
| `site.yml`                 | Main playbook — runs all roles in order              |
| `bootstrap.sh`             | One-time first-run script (port 22 → 2222)           |
| `inventory/generate.sh`    | Writes `hosts.ini` from live Pulumi stack output     |
| `inventory/hosts.ini`      | Active inventory (gitignored, generated)             |
| `group_vars/all.yml`       | Non-secret config (ports, image tags, paths, domain) |
| `secrets.yml`              | Vault-encrypted secrets (passwords, API tokens)      |
| `requirements.yml`         | Ansible collection dependencies                      |
| `ansible.cfg`              | Ansible defaults (inventory, SSH, vault)             |

---

## Roles

| Role        | Tags                    | What it does                                                            |
| ----------- | ----------------------- | ----------------------------------------------------------------------- |
| `common`    | `common`, `hardening`   | OS hardening: sshd, iptables, fail2ban, sysctl, swap, auditd, AppArmor |
| `docker`    | `docker`                | Docker CE + Compose plugin; daemon config                               |
| `infra`     | `infra`, `services`     | Shared Postgres 17 + Redis; `init.sql` is an optional bootstrap hook |
| `komodo`    | `komodo`, `services`    | Komodo + FerretDB stack; ongoing stack lifecycle managed in Komodo |

---

## Adding your own app stack (optional)

1. Add a compose file in your own stack path (this repo only curates `stacks/traefik`)
2. Add your app stack to the shared `shared_docker_network` (default: `internal-network`) and set a stable service alias
3. Add or update routing in `../stacks/traefik/dynamic.yml`
4. Add app secrets in Komodo Variables
5. If needed, add bootstrap SQL in `roles/infra/templates/init.sql.j2`
6. Deploy the app stack from Komodo

---

## Troubleshooting

**Connection refused on the hardened SSH port**
Bootstrap has not run yet, or it did not complete both phases. Run `./bootstrap.sh` again.

**Connection refused on the initial SSH port**
Cloud-init may still be running right after `pulumi up`. Wait 60-90 seconds and retry `./bootstrap.sh`.

**Traefik: certificate not issued**
The Cloudflare API token needs `Zone -> DNS -> Edit` scope for the target zone. Check Komodo Variables for `CLOUDFLARE_API_TOKEN`.

**Komodo not reachable at its subdomain**
Check that the Traefik stack is running in Komodo, the Komodo stack is attached to `shared_docker_network` (default: `internal-network`) with alias `komodo`, and there is a matching route in `stacks/traefik/dynamic.yml`.
