# ansible/

Provisions the server after Pulumi creates the VM. Runs in order: OS hardening → Docker → shared Postgres + Redis → Komodo → app scaffolding → Caddy.

## Prerequisites

- Ansible 2.13+ (`pip install ansible`)
- VM running with public IP from `pulumi stack output`
- SSH key at `~/.ssh/id_ed25519`

## Setup

```bash
cd ansible
cp inventory/hosts.ini.example inventory/hosts.ini   # paste server IP
cp secrets.yml.example secrets.yml                   # fill in all values
```

## Run

```bash
# Full provisioning (new server)
ansible-playbook site.yml \
  --extra-vars "@secrets.yml" \
  --extra-vars "ansible_become_password={{ deploy_password }}"

# Re-run a specific role
ansible-playbook site.yml \
  --extra-vars "@secrets.yml" \
  --extra-vars "ansible_become_password={{ deploy_password }}" \
  --tags caddy
```

## Roles

| Role | Tags | Does |
|------|------|------|
| `common` | `common`, `hardening` | Deploy user, SSH on port 2222, iptables, fail2ban, swap, auditd |
| `docker` | `docker` | Docker CE ARM64 |
| `infra` | `infra`, `services` | Shared Postgres 16 + Redis, per-app databases |
| `komodo` | `komodo`, `services` | Komodo + FerretDB (MongoDB adapter over Postgres) |
| `sure` | `sure`, `services` | Config dirs |
| `gitea` | `gitea`, `services` | Config dirs, rootless on port 3001/2223 |
| `databasus` | `databasus`, `services` | Config dirs |
| `n8n` | `n8n`, `services` | `/opt/n8n` dir |
| `caddy` | `caddy`, `services` | xcaddy build with Cloudflare DNS plugin, Caddyfile, systemd |

`--tags services` runs all service roles at once.

## Key files

- `group_vars/all.yml` — domain, timezone, ports, other non-secret config
- `secrets.yml` — gitignored, copy from `secrets.yml.example`
- `inventory/hosts.ini` — gitignored, copy from example

## Notes

**Caddy** is built via xcaddy with the Cloudflare DNS plugin for DNS-01 ACME — no port 80 needed. Update `roles/caddy/templates/Caddyfile.j2` to change routing, then `--tags caddy`.

**Postgres** — all apps share one container. Databases and users are created by `roles/infra/templates/init.sql.j2` on first run.

**FerretDB** — Komodo needs MongoDB; FerretDB provides a compatible API backed by Postgres. No extra config needed.

## Adding a new app

1. `ansible/roles/<name>/tasks/main.yml` — create `/opt/<name>` with correct ownership
2. `group_vars/all.yml` — add port variable
3. `roles/caddy/templates/Caddyfile.j2` — add vhost
4. `roles/infra/templates/init.sql.j2` — add DB + user if needed
5. `site.yml` — add role (before caddy)
6. Run: `--tags "infra,caddy,<name>"`

## Troubleshooting

**SSH refused on port 2222** — `common` moves SSH from 22 to 2222. Use 22 before the first run, 2222 after.

**Caddy can't get a certificate** — check `cloudflare_api_token` has `Zone:DNS:Edit`. Logs: `sudo journalctl -u caddy -f`

**Komodo unreachable** — `docker ps | grep komodo`, then `sudo caddy validate --config /etc/caddy/Caddyfile`
