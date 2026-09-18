# Papra Stack

Compose file: `stacks/papra/compose.yaml`

[Papra](https://papra.app) is a lightweight, self-hosted document management system (DMS) built on Hono. This stack replaces the heavier Paperless-ngx deployment with a lighter alternative.

## In Komodo

1. Create or open the `papra` stack.
2. Set compose path to `stacks/papra/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<PAPRA_HOST>`.

## Stack environment variables

- `PAPRA_HOST` (required): public hostname. Example: `papra.fewa.app`.
- `PAPRA_AUTH_SECRET` (required): auth secret. Generate with: `openssl rand -hex 32`.
- `TZ` (optional): timezone. Default: `UTC`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## Data

Persistent data is stored in the `papra_data` volume (both the database and documents).
Backup this volume to preserve your documents and metadata.

## Security

This stack includes Docker security hardening:

- **Memory limits**: `mem_limit` and `memswap_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit: 100` prevents fork bombs

Uses the rootless Papra image (`ghcr.io/papra-hq/papra:latest`) by default for improved security.