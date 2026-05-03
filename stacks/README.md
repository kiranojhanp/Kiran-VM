# stacks

This directory contains app stacks deployed from Komodo.

## What to do in Komodo

Use the same flow for every stack (`actual`, `audiobookshelf`, `authentik`, `garage`, `wealthfolio`, `jobops`, `mealie`, `openwebui`, `paperlessngx`, `uptime-kuma`, `vikunja`, `vaultwarden`, `wallos`):

1. Create the stack in Komodo (or open the existing one).
2. Set run directory to `stacks/<stack-name>`.
3. Set variables in the stack Environment section.
4. Deploy (or Redeploy).
5. After repo changes, run `task verify` locally, then redeploy in Komodo.

`task verify` checks infra, Traefik, and Komodo reachability.

## Auto-Deploy on Push to Main

Komodo pulls from GitHub automatically when you push to `main`. Setup:

1. In Komodo settings, enable the "Repository Webhook" feature and note the webhook URL.
2. Add these GitHub repository secrets:
   - `KOMODO_REPO_WEBHOOK_URL`: Komodo's repo webhook URL
   - `KOMODO_REPO_WEBHOOK_SECRET`: Secret for HMAC signature verification
3. That's it! Pushes to `main` trigger Komodo to pull the latest code.

See `.github/workflows/repo-deploy.yml` for the GitHub Actions workflow.

## Where each variable belongs

Use this split:

- Komodo stack environment: app runtime values used in `stacks/*/compose.yaml`.
- `provision/secrets.yml` (ansible-vault): platform secrets (`cloudflare_api_token`, `komodo_*`, shared DB/Redis passwords).
- Pulumi config (`infra` stack): OCI and infrastructure values (`oci:*`, `kiran-vm-infra:*`).

Komodo platform variables are not set per app stack. Provisioning renders them from `provision/secrets.yml` and `provision/group_vars/all.yml` into `/opt/komodo/.env` (for example: `KOMODO_WEBHOOK_SECRET`, `KOMODO_JWT_SECRET`, `KOMODO_INIT_ADMIN_USERNAME`, `KOMODO_INIT_ADMIN_PASSWORD`, `PERIPHERY_CORE_PUBLIC_KEYS`).

If a compose file references `${...}`, set it in that stack's Komodo Environment unless that stack README says otherwise.

## Shared variables used by multiple stacks

- `SHARED_DOCKER_NETWORK` (default `internal-network`): network for Traefik and app stacks.
- `SHARED_INFRA_NETWORK` (default `infra_net`): only for stacks that need shared Postgres or Redis.
- `TZ` (default `UTC`): timezone for stacks that expose timezone settings.
- `PUID` / `PGID` (default `1000`): UID/GID mapping for containers that support it.

## Shared Database

When adding a new stack that needs PostgreSQL, see [DATABASE.md](DATABASE.md) for instructions on creating a database user and database on the centralized Postgres instance.

## Stack docs

- [Actual](actual/README.md)
- [Audiobookshelf](audiobookshelf/README.md)
- [Authentik](authentik/README.md)
- [Garage](garage/README.md)
- [Wealthfolio](wealthfolio/README.md)
- [JobOps](jobops/README.md)
- [Mealie](mealie/README.md)
- [Media Stack](media-stack/README.md) (AIOMetadata + Decypharr + Poster Cache)
- [Media Server](media-server/README.md) (Plex + Sonarr + Radarr + Prowlarr)
- [Open WebUI](openwebui/README.md)
- [Paperless-ngx](paperlessngx/README.md)
- [Uptime Kuma](uptime-kuma/README.md)
- [Vikunja](vikunja/README.md)
- [Vaultwarden](vaultwarden/README.md)
- [Wallos](wallos/README.md)

Traefik is provisioned from `provision/roles/traefik/*`, not as a Komodo app stack.

## Required stack rules

- One app per stack and one stack per hostname (no duplicate `Host(...)` labels).
- Keep HTTPS labels in place (`entrypoints=websecure`, `tls=true`, `tls.certresolver=letsencrypt`).
- Avoid custom CSP labels unless an app strictly needs them.

`task verify` also fails if duplicate Traefik host routes are detected.
