# Penpot Stack

Compose file: `stacks/penpot/compose.yaml`

[Penpot](https://penpot.app) is an open-source design and prototyping platform for product teams. This stack runs the full Penpot suite (frontend, backend, admin-console, MCP, exporter) against the shared infra Postgres and Redis.

## In Komodo

1. Create or open the `penpot` stack.
2. Set run directory to `stacks/penpot`.
3. Set compose path to `stacks/penpot/compose.yaml`.
4. Add the variables below in the stack Environment.
5. Deploy (or Redeploy), then open `https://penpot.fewa.app`.

## Stack environment variables

- `PENPOT_HOST` (required): public hostname. Example: `penpot.fewa.app`.
- `PENPOT_SECRET_KEY` (required): master key used to derive subsystem keys. Generate with `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`.
- `PENPOT_DB_PASSWORD` (required): password for the `penpot` Postgres user on the shared infra DB. Use the shared `shared_postgres_password` from `provision/secrets.yml`.
- `PENPOT_REDIS_PASSWORD` (required): password for the shared infra Redis (`redis_password` from `provision/secrets.yml`).
- `PENPOT_VERSION` (optional): image version tag. Default: `2.18`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `SHARED_INFRA_NETWORK` (optional): shared infra network for Postgres/Redis. Default: `infra_net`.

## Database & Redis

Penpot uses the shared centralized Postgres (`infra-postgres-1`) and Redis (`infra-redis-1`).

The `penpot` database and user are provisioned automatically via `postgres_databases_list` in `provision/group_vars/all.yml`. Run `task update` to re-provision infra and create the database. See [DATABASE.md](../DATABASE.md) for details.

## Data

User-uploaded assets are stored in the `penpot_assets` named volume (mounted to `/opt/data/assets`). Back this up to preserve uploaded images/SVG clips.

## First-time setup

On first visit, Penpot lets you create an admin account in the browser. If registration is disabled, create a profile via the CLI:

```bash
docker exec -ti <penpot-backend-container> python3 manage.py create-profile
```

## Notes

- Traefik routes to the `penpot-frontend` service on port 8080. WebSocket endpoints (`/ws/notifications`, `/mcp/ws`) are handled by Traefik automatically.
- The `disable-email-verification` flag is set for a simple first deploy. For a production instance behind HTTPS, consider configuring real SMTP and enabling email verification.
- HTTPS is terminated at Traefik; `PENPOT_PUBLIC_URI` is set to `https://${PENPOT_HOST}` so Penpot issues secure session cookies.

## Security

This stack includes Docker security hardening:

- **Memory limits**: `mem_limit` and `memswap_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit` prevents fork bombs