# Backrest Stack

Compose file: `stacks/backrest/compose.yaml`

## In Komodo

1. Create or open the `backrest` stack.
2. Set compose path to `stacks/backrest/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<BACKREST_HOST>`.

## Initial setup in Backrest UI

1. Create the first Backrest admin user.
2. Add a repository pointing to `/opt/backup/restic-repo`.
3. Verify snapshot listing works before creating plans.
4. Keep systemd timers as source of truth until Backrest pilot is validated.

## Stack environment variables

- `BACKREST_HOST` (required): public hostname. Example: `backrest.fewa.app`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `TZ` (optional): timezone. Default: `UTC`.

Backrest mounts these host paths:

- `/opt/backup` (restic repository and scripts)
- `/var/backups/postgres/shared` (database dumps)
- `/var/lib/docker/volumes` (Docker volumes, read-only)
