# stacks

This directory holds app stacks you run from Komodo.

## What to do in Komodo

You will do the same basic flow for each stack (`actual`, `mealie`, `openwebui`, `paperlessngx`, `portabase`, `vikunja`, `vaultwarden`):

1. Open Komodo and create the stack (or open the existing one).
2. Point it to the correct compose file (`stacks/<stack-name>/compose.yaml`).
3. Set variables in that stack's Environment section.
4. Deploy (or Redeploy).
5. After any repo change, run `task verify` locally, then redeploy from Komodo.

`task verify` checks infra, Traefik, and Komodo reachability. App-level checks stay with each stack.

## Where each variable belongs

Use this split to avoid mixing concerns:

- Komodo stack environment: app runtime values used by `stacks/*/compose.yaml` (hostnames, app secrets, runtime settings).
- `provision/secrets.yml` (ansible-vault): platform secrets (`cloudflare_api_token`, `komodo_*`, shared DB/Redis passwords).
- Pulumi config (`infra` stack): OCI and infrastructure values (`oci:*`, `kiran-vm-infra:*`).

Komodo platform variables are not set in each app stack. Provisioning renders them from `provision/secrets.yml` and `provision/group_vars/all.yml` into `/opt/komodo/.env` (for example: `KOMODO_PASSKEY`, `KOMODO_WEBHOOK_SECRET`, `KOMODO_JWT_SECRET`, `KOMODO_INIT_ADMIN_USERNAME`, `KOMODO_INIT_ADMIN_PASSWORD`).

If a compose file references `${...}`, set it in that stack's Komodo Environment unless the stack README says otherwise.

## Shared variables used by multiple stacks

- `SHARED_DOCKER_NETWORK` (default `internal-network`): network used by Traefik and app stacks.
- `SHARED_INFRA_NETWORK` (default `infra_net`): only for stacks that need shared Postgres or Redis.
- `TZ` (default `UTC`): timezone for stacks that expose timezone settings.
- `PUID` / `PGID` (default `1000`): UID/GID mapping for containers that support it.

## Stack docs

- `stacks/actual/README.md`
- `stacks/mealie/README.md`
- `stacks/openwebui/README.md`
- `stacks/paperlessngx/README.md`
- `stacks/portabase/README.md`
- `stacks/vikunja/README.md`
- `stacks/vaultwarden/README.md`

Traefik is provisioned from `provision/roles/traefik/*`; it is not an app stack in Komodo.

## Required stack rules

- One app per stack and one stack per hostname (no duplicate `Host(...)` labels).
- Keep HTTPS labels in place (`entrypoints=websecure`, `tls=true`, `tls.certresolver=letsencrypt`).
- Avoid custom CSP labels unless an app strictly needs them.

`task verify` fails if duplicate Traefik host routes are detected.
