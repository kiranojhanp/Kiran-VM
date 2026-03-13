# kiran-vm

A practical, minimal self-hosted VM baseline on Oracle Cloud Always Free.

Core pipeline:

```
Pulumi -> Provision (includes Traefik) -> Komodo app stacks
```

Task commands are split into modular includes under `taskfiles/` for maintainability (`core.yml`, `infra.yml`, `server.yml`, `integrations.yml`).

Scope by design:
- Pulumi creates VM + network
- Ansible hardens host + installs Docker + Komodo + Traefik ingress
- This repo curates ingress defaults and base shared services; other apps are user-managed via Docker/Komodo

Why Komodo is not in `stacks/`:
- Komodo is part of base host provisioning (Ansible role) so control-plane boot always exists before stack deploy workflows run.

## Portability contract

If you want to run this in another OCI account or region, start with the vars in `Taskfile.yml`.

Those vars are the source of truth for:
- VM shape/CPU/RAM defaults
- network CIDRs and open ports
- bootstrap SSH port and hardened SSH port
- Ubuntu image defaults
- domain and DNS defaults (`DOMAIN_NAME_DEFAULT`, `CLOUDFLARE_ZONE_ID_DEFAULT`)
- Traefik certificate/contact defaults (`ACME_EMAIL_DEFAULT`, `KOMODO_SUBDOMAIN_LABEL`)
- Pulumi-managed DNS subdomains (`DNS_SUBDOMAIN_LABELS`)

`task prepare` (or `task sync` + `task init`) generates `infra/constants.py` and Traefik stack files from those vars. `infra/__main__.py` and `stacks/traefik/*.yml` consume the generated values.

## Minimal setup (first run)

1) Prepare stack

```bash
task prepare

# set required Pulumi config (OCI credentials + sshPublicKey)
# see infra/README.md for exact commands
```

2) Push full deployment

```bash
task push
```

Optional preflight-only check:

```bash
task doctor
```

After that, SSH moves to the hardened port from generated `infra/constants.py` (default `2222`).

## Start Here checklist

Use this if you want a single path from zero to running server.

1. Install prerequisites and Task (`task --list` should work).
2. Configure OCI + Pulumi values (follow `infra/README.md`).
3. Run deploy flow from repo root:

```bash
ansible-vault edit provision/secrets.yml
task push
```

4. Open `https://komodo.<your-domain>` and start adding your own stacks.

One-command flow for new environments:

```bash
STACK=<new-stack> BASE_STACK=kiran-self-hosting task push
```

## Task recipes

Install Task: https://taskfile.dev/docs/guide

```bash
task --list
```

Common usage (single VM, default stack `kiran-self-hosting`):

```bash
task prepare
task push
task update
task verify
task destroy CONFIRM=yes
```

Use explicit stack selection only when needed:

```bash
STACK=<new-stack> task prepare
STACK=<new-stack> task push
```

Canonical commands:
- `prepare` -> sync + stack init/select
- `doctor` -> preflight checks (tools, secrets, Pulumi config)
- `push` -> full deploy (infra + bootstrap + provision + verify)
- `update` -> reprovision + verify
- `verify` -> health checks only
- `destroy` -> safe infra teardown (requires `CONFIRM=yes`)

## Traefik defaults

Traefik is deployed automatically during `task provision` by the Ansible `traefik` role.

Before provisioning, set these in `Taskfile.yml` and run `task sync`:

- `DOMAIN_NAME_DEFAULT`
- `CLOUDFLARE_ZONE_ID_DEFAULT`
- `ACME_EMAIL_DEFAULT`
- `KOMODO_SUBDOMAIN_LABEL`
- `DNS_SUBDOMAIN_LABELS`

For certificate issuance, provide a Cloudflare token through one of:

- `cloudflare_api_token` in `provision/secrets.yml` (recommended)
- `CLOUDFLARE_API_TOKEN` env var on your controller
- `~/.cloudflare_pass` on your controller

## Docs map

- `infra/README.md`: Pulumi stack config and OCI details
- `provision/README.md`: server hardening/provisioning details
- `stacks/README.md`: traefik stack layout and conventions
- `llms.txt`: machine-oriented repo summary
