# kiran-vm

Portable self-hosted VM setup on Oracle Cloud Always Free.

Core pipeline:

```
Pulumi -> Ansible -> Komodo -> stacks/
```

## Portability contract

If you want to spin this up in a different OCI account/region with the same hardening defaults, start in `infra/constants.py`.

That file is the single source of truth for:
- VM shape/CPU/RAM defaults
- network CIDRs and open ports
- bootstrap SSH port and hardened SSH port
- Ubuntu image defaults

`infra/__main__.py` consumes those values and should usually not need edits.

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
cp ansible/secrets.yml.example ansible/secrets.yml
task hosts                 # alias: task inventory
task bootstrap             # alias: task harden
task provision             # alias: task ans
```

After this, SSH uses the hardened port from `infra/constants.py` (default `2222`).

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

Available targets cover the core flow:
- infra dependency sync + Pulumi lifecycle
- host inventory generation from Pulumi output
- first-run SSH bootstrap hardening
- full Ansible server provisioning

## Deploying apps

1. Open `https://komodo.<your-domain>`
2. For each app, create:
   - a Stack pointing to `stacks/<name>/compose.yaml`
   - a Procedure with stages: Pull Repo -> Deploy Stack
3. Add GitHub Action secret `KOMODO_WEBHOOK_<NAME>` per app

Any push to `stacks/<name>/` triggers the matching Komodo procedure.

## Docs map

- `infra/README.md`: Pulumi stack config and OCI details
- `ansible/README.md`: server hardening/provisioning details
- `stacks/README.md`: app stack layout and conventions
- `llms.txt`: machine-oriented repo summary
