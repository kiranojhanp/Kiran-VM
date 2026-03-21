# Vaultwarden Stack

Compose file: `stacks/vaultwarden/compose.yaml`

## In Komodo

1. Create or open the `vaultwarden` stack.
2. Set compose path to `stacks/vaultwarden/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<VAULTWARDEN_HOST>`.

## Stack environment variables

- `VAULTWARDEN_HOST` (required): public hostname. Example: `vaultwarden.fewa.app`.
- `VAULTWARDEN_SIGNUPS_ALLOWED` (optional): allow signup (`true` or `false`). Default: `false`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## Backups

Vaultwarden backups are managed by a separate stack: `stacks/vaultwarden-backup/compose.yaml`.
See `stacks/vaultwarden-backup/README.md` for R2 and `rclone` setup.
