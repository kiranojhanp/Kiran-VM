# stacks

This folder holds app stacks that Komodo deploys.

## Quickstart

If you change an app stack:

```bash
task verify
```

Then deploy/redeploy that stack from Komodo.

Core verification checks infra, Traefik, and Komodo. App-specific health checks are owned by each app stack/procedure.

## What is managed here

- `stacks/actual/compose.yaml` - Actual Budget stack
- `stacks/openwebui/compose.yaml` - Open WebUI stack
- `stacks/vaultwarden/compose.yaml` - Vaultwarden stack

Traefik is provisioned from `provision/roles/traefik/*`. It is not deployed from a Komodo stack.

Each Komodo stack should include Traefik labels for routing and TLS.
Each app must own exactly one hostname route (one stack per app/host).

App stacks are deployed through Komodo procedures/webhooks.

## Required stack rules

- One app per stack and one stack per hostname (no duplicate `Host(...)` labels across running containers).
- Always include Traefik labels for HTTPS routing (`entrypoints=websecure`, `tls=true`, `tls.certresolver=letsencrypt`).
- Do not add custom CSP labels unless strictly required by that app.

`task verify` fails if duplicate Traefik host routes are detected on the VM.

## Secret used here

- `cloudflare_api_token` from `provision/secrets.yml`
