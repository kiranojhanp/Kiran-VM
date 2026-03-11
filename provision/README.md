# ansible — server provisioning

Ansible playbooks for the production server running on Oracle Cloud (ARM64 Ubuntu).

Handles OS hardening, Docker, shared infrastructure (Postgres + Redis), and application scaffolding. Ongoing app deployments are managed by [Komodo](https://komo.do) after initial provisioning.

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

A fresh VM starts on the initial SSH port from `../infra/constants.py` (default `22`). The `common` role moves sshd to the hardened port from the same file (default `2222`). The bootstrap script keeps the initial port open during the transition, confirms the hardened port is reachable, then closes the initial port.

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
ansible-playbook site.yml
```

---

## Day-to-day usage

```bash
# Full playbook
ansible-playbook site.yml

# Dry run — shows what would change without applying it
ansible-playbook site.yml --check --diff

# Single role
ansible-playbook site.yml --tags docker
ansible-playbook site.yml --tags caddy

# All service roles at once
ansible-playbook site.yml --tags services

# Skip a role
ansible-playbook site.yml --skip-tags caddy
```

Available tags: `common`, `hardening`, `docker`, `infra`, `komodo`, `sure`, `gitea`, `databasus`, `n8n`, `caddy`, `services`

`generate.sh` and `bootstrap.sh` read shared SSH ports from `../infra/constants.py`, so Pulumi + Ansible stay aligned without duplicate hardcoded port values.

---

## Vault

Secrets are stored in `secrets.yml`, encrypted with [ansible-vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html). The vault password lives at `~/.vault_pass` (outside the repo, never committed). `ansible.cfg` reads it automatically.

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

`secrets.yml` is the source of truth for required secrets. Use `ansible-vault view secrets.yml` to inspect current keys, and `ansible-vault edit secrets.yml` to add/update values.

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
| `infra`     | `infra`, `services`     | Shared Postgres 17 + Redis; `init.sql` creates per-app databases        |
| `komodo`    | `komodo`, `services`    | Komodo + FerretDB stack; ongoing lifecycle managed by Komodo            |
| `sure`      | `sure`, `services`      | Directory scaffold; lifecycle managed by Komodo                         |
| `gitea`     | `gitea`, `services`     | Directory scaffold + custom templates; lifecycle managed by Komodo      |
| `databasus` | `databasus`, `services` | Directory scaffold; lifecycle managed by Komodo                         |
| `n8n`       | `n8n`, `services`       | Directory scaffold (uid 1000 for rootless); lifecycle managed by Komodo |
| `caddy`     | `caddy`, `services`     | xcaddy reverse proxy with Cloudflare DNS plugin; always runs last       |

---

## Adding a new app

1. Create `roles/<appname>/tasks/main.yml` — create `/opt/<appname>` with correct ownership
2. Add a virtual host block to `roles/caddy/templates/Caddyfile.j2`
3. Add the role to `site.yml` before the `caddy` role
4. Add secrets: `ansible-vault edit secrets.yml`
5. Add non-secret config to `group_vars/all.yml` (port, image, dir, subdomain)
6. Add the database to `roles/infra/templates/init.sql.j2` if needed
7. Run: `ansible-playbook site.yml`

Then configure the app stack in Komodo.

---

## Troubleshooting

**Connection refused on the hardened SSH port**
Bootstrap has not run yet, or it did not complete both phases. Run `./bootstrap.sh` again.

**Connection refused on the initial SSH port**
Cloud-init may still be running after `pulumi up`. Wait 60–90 seconds and retry `./bootstrap.sh`.

**Caddy: certificate not issued**
The Cloudflare API token needs `Zone → DNS → Edit` scope for the target zone. Check with `ansible-vault view secrets.yml`.

**Komodo not reachable at its subdomain**
Komodo binds to `127.0.0.1` and is only accessible via Caddy. Check that Caddy is running: `docker compose -f /opt/caddy/docker-compose.yml ps`.
