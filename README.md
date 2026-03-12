# kiran-vm

A practical, self-hosted VM setup on Oracle Cloud Always Free.

Core pipeline:

```
Pulumi -> Provision -> Komodo -> stacks/caddy
```

## Portability contract

If you want to run this in another OCI account or region, start with the vars in `Taskfile.yml`.

Those vars are the source of truth for:
- VM shape/CPU/RAM defaults
- network CIDRs and open ports
- bootstrap SSH port and hardened SSH port
- Ubuntu image defaults

`task sync` and `task init` generate `infra/constants.py` from those vars, and `infra/__main__.py` consumes the generated values.

## Minimal setup (first run)

1) Configure infra

```bash
task sync
task init STACK=kiran-prod   # first time only

# set required Pulumi config (OCI credentials + sshPublicKey)
# see infra/README.md for exact commands
```

2) Provision VM

```bash
task up                    # alias: task apply
```

3) Harden + provision server

```bash
task hosts                 # alias: task inventory
task bootstrap             # alias: task harden
task provision             # alias: task ans
```

After that, SSH moves to the hardened port from generated `infra/constants.py` (default `2222`).

## Start Here checklist

Use this if you want a single path from zero to running server.

1. Install prerequisites and Task (`task --list` should work).
2. Configure OCI + Pulumi values (follow `infra/README.md`).
3. Run infra lifecycle from repo root:

```bash
task sync
task init STACK=kiran-prod
task up STACK=kiran-prod
```

4. Generate inventory and harden SSH:

```bash
task hosts
task bootstrap
```

5. Add vault secrets and provision services:

```bash
ansible-vault edit provision/secrets.yml
task provision
```

6. Configure Komodo caddy stack/procedure (see `stacks/README.md`).

## Task recipes

Install Task: https://taskfile.dev/docs/guide

```bash
task --list
```

Stack-aware usage (defaults to `kiran-prod`):

```bash
task preview STACK=kiran-prod   # alias: task plan
task up STACK=kiran-prod        # alias: task apply
task destroy STACK=kiran-prod CONFIRM=yes   # alias: task nuke
```

The available targets cover the full flow:
- infra dependency sync + Pulumi lifecycle
- host inventory generation from Pulumi output
- first-run SSH bootstrap hardening
- full server provisioning

## Deploying caddy

1. Open `https://komodo.<your-domain>`
2. Create a Stack pointing to `stacks/caddy/compose.yaml`
3. Create a Procedure for caddy deploys
4. Add GitHub Action secret `KOMODO_WEBHOOK_CADDY`

Any push to `stacks/caddy/` triggers the caddy Komodo procedure.

## Docs map

- `infra/README.md`: Pulumi stack config and OCI details
- `provision/README.md`: server hardening/provisioning details
- `stacks/README.md`: app stack layout and conventions
- `llms.txt`: machine-oriented repo summary
