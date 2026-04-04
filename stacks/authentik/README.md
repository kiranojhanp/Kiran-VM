# Authentik Stack

Compose file: `stacks/authentik/compose.yaml`

## In Komodo

1. Create or open the `authentik` stack.
2. Set compose path to `stacks/authentik/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<AUTHENTIK_HOST>/if/flow/initial-setup/`.

## Stack environment variables

- `AUTHENTIK_HOST` (required): public hostname. Example: `auth.fewa.app`.
- `AUTHENTIK_SECRET_KEY` (required): stable random secret used for signing. Generate with `openssl rand -base64 60 | tr -d '\n'`.
- `AUTHENTIK_DB_NAME` (optional): database name. Default: `authentik`.
- `AUTHENTIK_DB_USER` (optional): database user. Default: `authentik`.
- `AUTHENTIK_DB_PASSWORD` (required): database password for `AUTHENTIK_DB_USER`.
- `SHARED_POSTGRES_HOST` (optional): shared Postgres host. Default: `postgres`.
- `SHARED_POSTGRES_PORT` (optional): shared Postgres port. Default: `5432`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `SHARED_INFRA_NETWORK` (optional): shared infra network for Postgres. Default: `infra_net`.
- `AUTHENTIK_TAG` (optional): pinned image tag. Default: `2026.2.2`.
- `AUTHENTIK_ERROR_REPORTING__ENABLED` (optional): send anonymized error reports. Default: `false`.
- `AUTHENTIK_DISABLE_UPDATE_CHECK` (optional): disable release checks. Default: `false`.
- `AUTHENTIK_OUTPOSTS__DISCOVER` (optional): docker/k8s auto-discovery for outposts. Default: `false`.

## Production notes

- Reuse shared Postgres by adding `authentik` to `postgres_databases_list` in `provision/group_vars/all.yml` and running `task update`.
- Keep `/data` persistent (`authentik_data` volume) for media, templates, and runtime state.
- Keep docker socket unmounted unless you explicitly need automatic outpost deployment.
- Do not mount `/etc/timezone` or `/etc/localtime` into authentik containers.
- The initial setup URL requires a trailing slash: `/if/flow/initial-setup/`.

## Recommended hardening after first login

1. Configure SMTP (`AUTHENTIK_EMAIL__*`) for recovery and operational alerts.
2. Limit public signup and review default flows/policies.
3. Add monitoring for `https://<AUTHENTIK_HOST>/` and alert on downtime.
4. Keep image tags pinned and upgrade intentionally.
