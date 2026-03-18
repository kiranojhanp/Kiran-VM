# Paperless-ngx Stack

Compose file: `stacks/paperlessngx/compose.yaml`

## In Komodo

1. Create or open the `paperlessngx` stack.
2. Set compose path to `stacks/paperlessngx/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<PAPERLESS_HOST>`.

## Stack environment variables

- `PAPERLESS_HOST` (required): public hostname. Example: `paperless.fewa.app`.
- `PAPERLESS_DB_NAME` (required): database name.
- `PAPERLESS_DB_USER` (required): database user.
- `PAPERLESS_DB_PASSWORD` (required): database password.
- `SHARED_POSTGRES_HOST` (optional): shared Postgres host. Default: `postgres`.
- `SHARED_REDIS_HOST` (optional): shared Redis host. Default: `redis`.
- `TZ` (optional): timezone. Default: `UTC`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `SHARED_INFRA_NETWORK` (optional): shared infra network. Default: `infra_net`.
