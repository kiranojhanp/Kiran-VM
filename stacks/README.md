# stacks

Application stacks managed by Komodo live here.

## Quickstart

If you change an app stack:

```bash
task update
task verify
```

That is all most users need.

## What is managed here

- `stacks/actual/compose.yaml` - Actual Budget stack

Traefik is provisioned from `provision/roles/traefik/*` and is not deployed from a Komodo stack.

Komodo-managed stacks should declare Traefik labels for routing and TLS.

Application stacks are deployed through Komodo procedures/webhooks.

## Secret used here

- `cloudflare_api_token` from `provision/secrets.yml`
