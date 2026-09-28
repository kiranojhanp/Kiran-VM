# Yuvomi Stack

Compose file: `stacks/finance-stack/yuvomi/compose.yaml`

[Yuvomi](https://yuvomi.cloud/install.html#docker) is a self-hosted household / family planner (budgets, tasks, calendar & contacts sync, document storage). This stack is part of the **finance-stack** group.

## In Komodo

1. Create or open the `yuvomi` stack.
2. Set the run directory to `stacks/finance-stack/yuvomi`.
3. Set compose path to `stacks/finance-stack/yuvomi/compose.yaml`.
4. Add the variables below in the stack Environment.
5. Deploy (or Redeploy), then open `https://yuvomi.fewa.app`.

## Stack environment variables

- `YUVOMI_HOST` (required): public hostname. Example: `yuvomi.fewa.app`.
- `SESSION_SECRET` (required): session cookie signing secret. Generate with `openssl rand -base64 48`.
- `DB_ENCRYPTION_KEY` (optional, irreversible): AES-256 encryption key for the SQLite database. Generate with `openssl rand -hex 32`. Back it up — losing it makes the data unrecoverable. Leave empty for an unencrypted database.
- `SESSION_SECURE` (optional): set to `true` when behind an HTTPS reverse proxy (Traefik). Default: `true`.
- `TRUST_PROXY` (optional): reverse-proxy hop count. Default: `1` (correct for Traefik in Docker).
- `TZ` (optional): timezone. Default: `UTC`.
- `WEATHER_LAT` / `WEATHER_LON` / `WEATHER_CITY` (optional): weather widget coordinates.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## Data

Persistent data is stored in the `yuvomi_data` and `yuvomi_backups` named volumes, mounted to `/data` and `/backups`. Back these up to preserve your database and backups.

## First-time setup

On the first visit, Yuvomi walks you through creating your admin account in the browser. The container runs on port 3000 behind Traefik (HTTPS, `websecure` entrypoint).

## Backups

Yuvomi has built-in automated backups (daily, 7 kept) that write to `/backups`. Optionally configure a WebDAV target or local folder for document storage as described in the [Yuvomi install docs](https://yuvomi.cloud/install.html#docker).

## Security

This stack includes Docker security hardening:

- **Memory limits**: `mem_limit` and `memswap_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit: 200` prevents fork bombs