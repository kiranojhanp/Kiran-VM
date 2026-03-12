# stacks/

Docker Compose stacks managed by [Komodo](https://komo.do).

This repo officially supports one managed stack: `caddy`.

## Supported stack

- `stacks/caddy/compose.yaml`
- `stacks/caddy/Caddyfile`

`caddy` runs with `network_mode: host` so it can proxy host-local services bound to `127.0.0.1:<port>`.

## Deploying caddy

**Automatically** - push changes under `stacks/caddy/**` to `main`. GitHub Actions triggers the Komodo caddy procedure.

**Manually** - Komodo UI -> Stacks -> caddy -> Deploy.

## Secrets

Runtime secrets live in Komodo (Settings -> Variables), referenced in compose as `[[SECRET_NAME]]`.

Required for caddy:

- `CLOUDFLARE_API_TOKEN` for DNS-01 certificate issuance.

## Routing updates

Edit `stacks/caddy/Caddyfile` to add or change domains and upstreams.

## Troubleshooting

**Certificate not issued** - Cloudflare API token needs `Zone -> DNS -> Edit` for the target zone.

**502 Bad Gateway** - upstream container is not running or not listening on the proxied host-local port.

**Webhook not firing** - check GitHub Actions logs and verify `KOMODO_WEBHOOK_CADDY` is set.
