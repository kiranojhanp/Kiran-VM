# Vaultwarden Backup Stack

Compose file: `stacks/vaultwarden-backup/compose.yaml`

This stack runs `ttionya/vaultwarden-backup` independently from the `vaultwarden` app stack and uploads backups to Garage S3 via rclone.

## In Komodo

1. Create or open the `vaultwarden-backup` stack.
2. Set run directory to `stacks/vaultwarden-backup`.
3. Set compose path to `stacks/vaultwarden-backup/compose.yaml`.
4. Add the variables below in the stack Environment.
5. Add `VW_BACKUP_ZIP_PASSWORD` in Komodo as a secret variable.
6. Deploy (or Redeploy).

## Configure rclone for Garage S3

The rclone config lives in the `vaultwarden_backup_rclone_data` Docker volume. To set it up:

```bash
docker run --rm -it -v vaultwarden_backup_rclone_data:/config rclone/rclone:latest config --config /config/rclone.conf
```

Use remote name `garage` (default). Example settings:

- `type`: `s3`
- `provider`: `Other`
- `access_key_id` / `secret_access_key`: Garage S3 credentials
- `endpoint`: `https://s3.fewa.app`
- `region`: `ap-southeast-1`
- `force_path_style`: `true`

Also create the `vaultwarden-backups` bucket in Garage and grant your access key permission to it.

## Stack environment variables

- `VW_BACKUP_RCLONE_REMOTE_NAME` (optional): rclone remote name. Default: `garage`.
- `VW_BACKUP_RCLONE_REMOTE_DIR` (optional): target path in remote storage. Default: `postgres-backup/vaultwarden/prod/`.
- `VW_BACKUP_CRON` (optional): backup schedule. Default: `17 3 * * *`.
- `VW_BACKUP_ZIP_ENABLE` (optional): archive backups (`TRUE`/`FALSE`). Default: `TRUE`.
- `VW_BACKUP_ZIP_TYPE` (optional): archive format (`zip`/`7z`). Default: `7z`.
- `VW_BACKUP_FILE_SUFFIX` (optional): unique suffix format. Default: `%Y%m%d-%H%M%S`.
- `VW_BACKUP_KEEP_DAYS` (optional): retention days (`0` keeps all). Default: `30`.
- `VW_BACKUP_PING_URL` (optional): success/failure monitor endpoint.
- `VW_BACKUP_ZIP_PASSWORD` (recommended secret): ZIP archive password.
- `VAULTWARDEN_DATA_VOLUME` (optional): source Vaultwarden data volume name. Default: `vaultwarden_vaultwarden_data`.
- `TZ` (optional): timezone. Default: `UTC`.

## First-run checks

1. Trigger one manual backup after deploy: `docker exec vaultwarden-backup-vaultwarden-backup-1 /bin/bash /app/backup.sh`
2. Confirm backup objects appear in Garage bucket.
3. Confirm retention cleanup works after the configured window.
4. Test restore in a non-production Vaultwarden instance before relying on the backups.
