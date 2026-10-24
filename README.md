# kiran-vm

Self-hosting baseline for Oracle Cloud Always Free.

## Quickstart

Run this from repo root.

```bash
# 1) one-time on your machine
echo 'your-ansible-vault-password' > ~/.vault_pass
chmod 600 ~/.vault_pass

# 2) create and fill encrypted secrets
task secrets:init
task secrets:edit

# 3) prepare stack and local constants
task prepare

# 4) set Pulumi config (one-time per stack)
# see infra/README.md for exact commands

# 5) deploy everything
task push
```

When it finishes, open `https://komodo.<your-domain>`.
`task push` temporarily opens SSH 22 for first-boot bootstrap and then closes it.

## Daily use

```bash
task update    # re-apply provisioning + verify
task verify    # health checks only
task backup:health
task destroy CONFIRM=yes
```

## Backup commands

```bash
# Postgres (WAL-G)
task backup:postgres:health
task backup:postgres:list
task backup:postgres:run
task backup:postgres:restore
task backup:postgres:restore:pitr PITR_TIMESTAMP='2025-03-21 10:00:00' TARGET_DIR=/tmp/wal-g-restore-pitr

# SQLite services (Litestream)
task backup:sqlite:health
task backup:sqlite:status SERVICE=vaultwarden
# Show Garage bucket object stats for the service backup
task backup:sqlite:versions SERVICE=vaultwarden
task backup:sqlite:restore SERVICE=vaultwarden TARGET_DIR=/tmp/litestream-restore
task backup:sqlite:restore:pitr SERVICE=vaultwarden PITR_TIMESTAMP='2025-03-21 10:00:00' TARGET_DIR=/tmp/litestream-restore-pitr
```

Legacy task names (`walg:*`, `litestream:*`, `backup:walg:*`, `backup:litestream:*`) are still available as aliases.

## Non-default stack

Default stack is `kiran-self-hosting`.

```bash
STACK=<name> BASE_STACK=kiran-self-hosting task push
```

## What this repo manages

- Pulumi: VM, network, and DNS records
- Ansible: hardening, Docker, Komodo, and Traefik
- Komodo: app stacks you deploy with webhooks/procedures

## Docs

- `infra/README.md` - Pulumi setup and required config keys
- `provision/README.md` - provisioning and secrets workflow
- `stacks/README.md` - Komodo-managed app stacks and Traefik label routing
- `provision/README.md` - backup operations (Postgres + SQLite)
- `llms.txt` - concise machine-readable project map

## Disaster Recovery

### Delete Protection
The VM instance is protected from accidental `pulumi down`:

```bash
# To delete the VM, you must first unprotect it:
cd infra
pulumi state unprotect urn:pulumi:kiran-self-hosting::kiran-vm-infra::oci:Core/instance:Instance::kiran-self-hosting-vm

# Then you can destroy
cd infra
pulumi down
```

### Backup Status
| Service        | Backup Method           | Status |
| -------------- | ---------------------- | ------ |
| PostgreSQL    | WAL-G → Garage (R2)    | ✅     |
| Vaultwarden   | Litestream → Garage    | ✅     |
| Actual Budget | Litestream → Garage    | ✅     |
| Wallos        | Litestream → Garage    | ✅     |
| Wealthfolio   | Litestream → Garage    | ✅     |

### Encryption
- **OCI Block Volumes**: AES-256 encrypted at rest (default)
- **Traffic to Garage**: HTTPS
- **Garage internal**: Secret Handshake encryption
