# stacks/

Docker Compose files for each app, managed by [Komodo](https://komo.do). A push to `main` triggers GitHub Actions, which calls the matching Komodo webhook and redeploys that stack.

App stacks bind to `127.0.0.1:<port>` (Caddy proxies them) and join `infra_net` to reach shared Postgres and Redis.

`caddy` is also managed as a stack, but it is a special case: it runs with `network_mode: host` so it can proxy host-local app ports.

## Deploying

**Automatically** - push a change to `stacks/<name>/`. GitHub Actions runs `task komodo:trigger` and fires the Komodo procedure for that stack only.

**Manually** - Komodo UI -> Stacks -> select stack -> Deploy.

## Secrets

Runtime secrets live in Komodo (Settings → Variables), referenced in `compose.yaml` as `[[SECRET_NAME]]`. They're never in this repo.

To add one: Komodo → Settings → Variables → New Variable, then reference it in the compose file and redeploy.

Stack-specific env vars (not global secrets) go in the Stack's Environment tab in Komodo UI.

## n8n gotchas

**Timezone** - use `N8N_TZ`, not `TZ`. Komodo treats `TZ` as reserved and silently drops it.

**Encryption key** - `N8N_ENCRYPTION_KEY` must be set in Komodo Variables. If this key is ever lost, all stored n8n credentials are permanently unrecoverable. Keep a copy in a password manager.

## caddy gotchas

**Cloudflare token** - set `CLOUDFLARE_API_TOKEN` in Komodo Variables; Caddy uses it for DNS-01 cert issuance.

**Routing updates** - edit `stacks/caddy/Caddyfile` directly. Changes trigger Caddy redeploy via the stack webhook.

## Adding a new stack

1. `stacks/<name>/compose.yaml` — bind to `127.0.0.1:<port>`, join `infra_net`, use `[[SECRET]]` for secrets
2. Add or update routing in `stacks/caddy/Caddyfile`
3. Komodo: create Stack + Procedure, copy webhook URL
4. GitHub: add `KOMODO_WEBHOOK_<NAME>` secret
5. `.github/workflows/deploy-stacks.yml`: add path filter for the new stack

## Troubleshooting

**502 Bad Gateway** - container is not running. Check `docker logs <container>` or Komodo -> Stacks -> Logs.

**`[[SECRET]]` shows literally** - variable name does not exist in Komodo Variables. Check for typos.

**Can't reach Postgres** - verify the container is on `infra_net`: `docker network inspect infra_net`. Check `compose.yaml` declares it as external. Use the actual container name (`docker ps | grep postgres`), not an assumed hostname.

**Webhook not firing** - check GitHub Actions logs and verify the path filter in `deploy-stacks.yml` matches the changed file.
