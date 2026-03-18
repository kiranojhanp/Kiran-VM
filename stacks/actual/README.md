# Actual Budget Stack

Compose file: `stacks/actual/compose.yaml`

## In Komodo

1. Create or open the `actual` stack.
2. Set compose path to `stacks/actual/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<ACTUAL_HOST>`.

## Stack environment variables

- `ACTUAL_HOST` (required): public hostname. Example: `actual.fewa.app`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

Do not set `ACTUAL_PORT` in Komodo. It is fixed to `5006` in compose.
