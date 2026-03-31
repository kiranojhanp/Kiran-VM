# Wallos Stack

Compose file: `stacks/wallos/compose.yaml`

## In Komodo

1. Create or open the `wallos` stack.
2. Set compose path to `stacks/wallos/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<WALLOS_HOST>`.

## Stack environment variables

- `WALLOS_HOST` (required): public hostname. Example: `wallos.fewa.app`.
- `TZ` (optional): timezone. Default: `UTC`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## Notes

- First visit: create an admin account in the web UI.
- Login uses the **username** you created during registration (not the email).
- Uses named Docker volumes (`wallos_db`, `wallos_logos`) to match other stacks and keep setup simpler in Komodo.
- Uses official in-container paths (`/var/www/html/db` and `/var/www/html/images/uploads/logos`).

## Backups

Wallos uses Litestream for continuous SQLite replication to Garage S3. This is managed via Ansible in `provision/roles/litestream-backup` with service name `wallos` and bucket `wallos-backups`.
