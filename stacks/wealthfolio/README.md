# Wealthfolio Stack

Compose file: `stacks/wealthfolio/compose.yaml`

## In Komodo

1. Create or open the `wealthfolio` stack.
2. Set compose path to `stacks/wealthfolio/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<WEALTHFOLIO_HOST>`.

## Stack environment variables

- `WEALTHFOLIO_HOST` (required): public hostname. Example: `wealthfolio.fewa.app`.
- `WF_CORS_ALLOW_ORIGINS` (required when auth is enabled): comma-separated allowed origins. Example: `https://wealthfolio.fewa.app`.
- `WF_SECRET_KEY` (required): encryption key generated with `openssl rand -base64 32`.
- `WF_AUTH_PASSWORD_HASH` (required): Argon2 password hash generated from your login password.
- `WF_DB_PATH` (optional): SQLite database path in container. Default: `/data/wealthfolio.db`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## First-time setup

1. Generate a secret key:

   ```bash
   openssl rand -base64 32
   ```

2. Generate an Argon2 hash for the login password (example):

   ```bash
   printf 'your-password' | argon2 yoursalt16chars! -id -e
   ```

3. Set `WF_SECRET_KEY` and `WF_AUTH_PASSWORD_HASH` in Komodo stack Environment.

## Notes

- Uses the `ghcr.io/afadil/wealthfolio:latest` image (Wealthfolio self-host build).
- Uses named Docker volume `wealthfolio_data` mounted to `/data` to persist the SQLite database.

## Backups

Wealthfolio uses Litestream for continuous SQLite replication to Garage S3. This is managed via Ansible in `provision/roles/litestream-backup` with service name `wealthfolio` and bucket `wealthfolio-backups`.
