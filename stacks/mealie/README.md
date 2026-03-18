# Mealie Stack

Compose file: `stacks/mealie/compose.yaml`

## In Komodo

1. Create or open the `mealie` stack.
2. Set compose path to `stacks/mealie/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<MEALIE_HOST>`.

## Stack environment variables

- `MEALIE_HOST` (required): public hostname. Example: `mealie.fewa.app`.
- `MEALIE_ALLOW_SIGNUP` (optional): allow public signup (`true` or `false`). Default: `true`.
- `TZ` (optional): timezone. Default: `UTC`.
- `PUID` (optional): user ID inside container. Default: `1000`.
- `PGID` (optional): group ID inside container. Default: `1000`.
- `MEALIE_MAX_WORKERS` (optional): worker count. Default: `1`.
- `MEALIE_WEB_CONCURRENCY` (optional): web concurrency. Default: `1`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
