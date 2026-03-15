# stacks

This folder holds app stacks that Komodo deploys.

## Quickstart

If you change an app stack:

```bash
task update
task verify
```

That is enough for normal day-to-day use.

## What is managed here

- `stacks/actual/compose.yaml` - Actual Budget stack

Traefik is provisioned from `provision/roles/traefik/*`. It is not deployed from a Komodo stack.

Each Komodo stack should include Traefik labels for routing and TLS.

App stacks are deployed through Komodo procedures/webhooks.

## Secret used here

- `cloudflare_api_token` from `provision/secrets.yml`
