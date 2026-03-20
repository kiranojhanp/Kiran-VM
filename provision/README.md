# provision

Ansible layer for hardening, Docker, shared services, Komodo, Traefik, and backups.

## Quickstart

From repo root:

```bash
task secrets:init   # first time only
task secrets:edit   # fill all values
task push
```

That is the normal path. `task push` handles bootstrap, provisioning, and verification.

## Common commands

```bash
task update
task verify
task provision:inventory
task provision:bootstrap   # only if you need to rerun first-boot SSH hardening
```

## Secrets

- Source of truth: `provision/secrets.yml` (encrypted)
- Template: `provision/secrets.example.yml`
- Edit with: `task secrets:edit`

Required keys are listed in the template. Keep `cloudflare_api_token` current there.
Use `common_deploy_ssh_public_key` for the deploy user's authorized key.

## If something breaks

- Cert issue: update `cloudflare_api_token` in secrets, then run `task update`.
- Komodo unreachable: run `task verify`, then check `task update` output.
