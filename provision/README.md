# provision

Ansible layer for hardening, Docker, shared services, Komodo, Traefik, and backups.

## Quickstart

From repo root:

```bash
task secrets:init   # first time only
task secrets:edit   # fill all values
task push
```

That is the normal path. `task push` handles bootstrap, provisioning, and verification.

## Common commands

```bash
task update
task verify
task provision:inventory
task provision:bootstrap   # only if you need to rerun first-boot SSH hardening
```

## Secrets

- Source of truth: `provision/secrets.yml` (encrypted)
- Template: `provision/secrets.example.yml`
- Edit with: `task secrets:edit`

Required keys are listed in the template. Keep `cloudflare_api_token` current there.
Use `common_deploy_ssh_public_key` for the deploy user's authorized key.

## If something breaks

- Cert issue: update `cloudflare_api_token` in secrets, then run `task update`.
- Komodo unreachable: run `task verify`, then check `task update` output.

## Backups

Task groups are organized by database type:

- `backup:postgres:*` - PostgreSQL backups via WAL-G
- `backup:sqlite:*` - SQLite backups via Litestream
- `backup:health` - runs both health checks

Legacy names (`walg:*`, `litestream:*`) still work as aliases.

### Postgres Backup (WAL-G)

Postgres runs with `archive_mode=on` — every WAL segment is pushed to Cloudflare R2 in real-time via `wal-g wal-push`. Base backups run on the 1st and 15th of each month via systemd timer.

All backup scripts live in `/opt/backup/scripts/` on the server. WAL-G runs inside the Postgres container (defined by `postgres_container_name` in `group_vars/all.yml`, default: `infra-postgres-1`), so Postgres data and the binary are always in sync.

### Taskfile commands

```bash
# Health check: timers, R2 connectivity, backup age
task backup:postgres:health

# List all backups in R2
task backup:postgres:list

# Run a base backup immediately (after a config change, before an upgrade)
task backup:postgres:run

# Run integrity check
task backup:postgres:check

# Restore the latest backup to /tmp/walg-restore on the server
task backup:postgres:restore

# Restore a specific backup
task backup:postgres:restore BACKUP_NAME=base_000000010000000000000037

# Point-in-time restore
task backup:postgres:restore:pitr PITR_TIMESTAMP='2025-03-21 10:00:00' TARGET_DIR=/tmp/wal-g-restore-pitr
```

### How it works

```
Postgres (container)
  archive_command = wal-g wal-push %p
  → WAL segments pushed continuously to R2

kiran-walg-backup.timer (1st & 15th, 3am)
  → /opt/backup/scripts/wal-g-backup.sh
    → docker exec <postgres_container_name> wal-g backup-push /var/lib/postgresql/data
    → Full base backup to R2

kiran-walg-prune.timer (1st of month, 4am)
  → /opt/backup/scripts/wal-g-prune.sh
    → docker exec <postgres_container_name> wal-g delete --retain-full 4 --keep-weekly 4 ...
    → Prunes old backups

kiran-walg-check.timer (Sunday, 5am)
  → /opt/backup/scripts/wal-g-check.sh
    → docker exec <postgres_container_name> wal-g backup-check
    → Verifies backup integrity
```

Replace `<postgres_container_name>` with the value from `group_vars/all.yml` (default: `infra-postgres-1`).

### Restore workflow

1. **List backups** to find what you need:
   ```bash
   task backup:postgres:list
   ```

2. **Restore to a temp directory** inside the Postgres container:
   ```bash
   task backup:postgres:restore
   # or specific backup:
   task backup:postgres:restore BACKUP_NAME=base_000000010000000000000037
   # or point-in-time:
   task backup:postgres:restore:pitr PITR_TIMESTAMP='2025-03-21 10:00:00' TARGET_DIR=/tmp/wal-g-restore-pitr
   ```
   Files are placed at `/tmp/wal-g-restore/` inside the container.

3. **Copy to the server** for inspection:
   ```bash
   docker cp <postgres_container_name>:/tmp/wal-g-restore/. /tmp/walg-restore/
   ```

4. **Inspect the restore** (no data written to Postgres):
   ```bash
   # Check what databases were backed up
   ls /tmp/walg-restore/backups/<timestamp>/

   # Verify dump integrity
   docker exec <postgres_container_name> pg_restore -U postgres -d postgres -f /dev/null /tmp/walg-restore/backups/<timestamp>/<db>.dump
   ```

5. **Promote to live** (only if restoring to a running Postgres):
   ```bash
   # Stop Postgres first
   docker exec <postgres_container_name> pg_ctl stop -D /var/lib/postgresql/data

   # Move old data dir and swap in restored data
   mv /var/lib/postgresql/data /var/lib/postgresql/data.broken
   mv /tmp/wal-g-restore /var/lib/postgresql/data
   chown -R postgres:postgres /var/lib/postgresql/data

   # Restart
   docker restart <postgres_container_name>
   ```

### Required secrets

Set these in `provision/secrets.yml` (`task secrets:edit`):

```yaml
backup_wal_g_s3_bucket: "my-bucket"           # R2 bucket name
backup_wal_g_s3_prefix: "postgres"            # folder inside bucket for Postgres backups
backup_wal_g_aws_endpoint: "https://...r2.cloudflarestorage.com"  # R2 endpoint (just host, no path)
backup_wal_g_s3_force_path_style: "true"
backup_wal_g_aws_access_key_id: "..."
backup_wal_g_aws_secret_access_key: "..."
backup_wal_g_aws_region: "auto"
backup_wal_g_password: "..."                  # WAL-G encryption password (separate from Postgres password)
```

### Retention

| Policy | Keep |
|--------|------|
| Full backups | 4 |
| Weekly | 4 |
| Monthly | 6 |
| Yearly | 1 |

### Troubleshooting

```bash
# Check timers are active
task backup:postgres:health

# Tail backup logs
journalctl -u kiran-walg-backup.service -n 50 --no-pager

# Check WAL archival is working (should show recent files)
docker exec <postgres_container_name> psql -U postgres -c "SELECT * FROM pg_stat_archiver;"

# Verify R2 connectivity from inside the container
docker exec <postgres_container_name> wal-g backup-list
```

### SQLite Backup (Litestream)

Litestream continuously replicates SQLite snapshots to Garage/R2 for services like Vaultwarden, Actual, Wallos, and Wealthfolio.

```bash
# Health check for all configured SQLite services
task backup:sqlite:health

# Check one service's timer and service status
task backup:sqlite:status SERVICE=vaultwarden

# List snapshots for one service
task backup:sqlite:versions SERVICE=vaultwarden

# Restore latest snapshot
task backup:sqlite:restore SERVICE=vaultwarden TARGET_DIR=/tmp/litestream-restore

# Point-in-time restore
task backup:sqlite:restore:pitr SERVICE=vaultwarden PITR_TIMESTAMP='2025-03-21 10:00:00' TARGET_DIR=/tmp/litestream-restore-pitr
```
