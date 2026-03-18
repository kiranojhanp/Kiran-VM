# Vikunja Stack

Compose file: `stacks/vikunja/compose.yaml`

## In Komodo

1. Create or open the `vikunja` stack.
2. Set compose path to `stacks/vikunja/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<VIKUNJA_HOST>`.

## Stack environment variables

- `VIKUNJA_HOST` (required): public hostname. Example: `vikunja.fewa.app`.
- `VIKUNJA_JWT_SECRET` (required): strong random secret for JWT.
- `VIKUNJA_DB_NAME` (required): database name.
- `VIKUNJA_DB_USER` (required): database user.
- `VIKUNJA_DB_PASSWORD` (required): database password.
- `SHARED_POSTGRES_HOST` (optional): shared Postgres host. Default: `postgres`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `SHARED_INFRA_NETWORK` (optional): shared infra network. Default: `infra_net`.
