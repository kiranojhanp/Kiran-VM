# kiran-vm

Self-hosting baseline for Oracle Cloud Always Free.

## Quickstart

Run this from repo root.

```bash
# 1) one-time on your machine
echo 'your-ansible-vault-password' > ~/.vault_pass
chmod 600 ~/.vault_pass

# 2) create and fill encrypted secrets
task secrets:init
task secrets:edit

# 3) prepare stack and local constants
task prepare

# 4) set Pulumi config (one-time per stack)
# see infra/README.md for exact commands

# 5) deploy everything
task push
```

When it finishes, open `https://komodo.<your-domain>`.
`task push` temporarily opens SSH 22 for first-boot bootstrap and then closes it.

## Daily use

```bash
task update    # re-apply provisioning + verify
task verify    # health checks only
task destroy CONFIRM=yes
```

## Non-default stack

Default stack is `kiran-self-hosting`.

```bash
STACK=<name> BASE_STACK=kiran-self-hosting task push
```

## What this repo manages

- Pulumi: VM, network, and DNS records
- Ansible: hardening, Docker, Komodo, and Traefik
- Komodo: app stacks you deploy with webhooks/procedures

## Docs

- `infra/README.md` - Pulumi setup and required config keys
- `provision/README.md` - provisioning and secrets workflow
- `stacks/README.md` - Komodo-managed app stacks and Traefik label routing
- `llms.txt` - concise machine-readable project map
