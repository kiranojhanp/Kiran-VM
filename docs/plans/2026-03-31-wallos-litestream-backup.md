# Wallos Litestream Backup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Wallos SQLite continuous backup to Garage S3 using the existing Litestream backup pattern already used for Vaultwarden and Actual.

**Architecture:** Reuse the shared `litestream-backup` Ansible role and register Wallos as another service instance in `provision/site.yml`. Configure service-specific values (service name, data volume path, pattern, bucket) and include Wallos in backup health checks. Keep stack-level docs aligned with operational behavior.

**Tech Stack:** Ansible roles/playbook, systemd services/timers, Litestream, Garage S3, Taskfile tasks.

---

### Task 1: Register Wallos Litestream backup role invocation

**Files:**
- Modify: `provision/site.yml`

**Step 1: Add role invocation**

Add a new `litestream-backup` role block for `wallos` in the same section as `vaultwarden` and `actual`.

**Step 2: Set Wallos-specific variables**

Set:
- `litestream_backup_enabled: true`
- `litestream_backup_service_name: wallos`
- `litestream_backup_data_volume: wallos_wallos_db`
- `litestream_backup_data_path: /var/lib/docker/volumes/wallos_wallos_db/_data`
- `litestream_backup_pattern: "*.db"`
- `litestream_backup_bucket: wallos-backups`

**Step 3: Validate YAML formatting**

Run: `task verify`

Expected: verification succeeds and no Ansible/yaml errors.

### Task 2: Document Wallos litestream settings in shared vars

**Files:**
- Modify: `provision/group_vars/all.yml`

**Step 1: Add Wallos litestream config entries**

Add non-secret Wallos backup variables near existing Litestream sections:
- `wallos_litestream_enabled: true`
- `wallos_litestream_backup_bucket: wallos-backups`
- `wallos_litestream_backup_path: prod/db`

**Step 2: Keep comments consistent**

Use the same style and intent comments as Vaultwarden/Actual sections.

### Task 3: Include Wallos in operational backup health checks

**Files:**
- Modify: `taskfiles/server.yml`

**Step 1: Extend service status checks**

Update `litestream:health` systemd status command to include `kiran-wallos-litestream.service`.

**Step 2: Extend timer checks**

Update timer grep expression to include `wallos-litestream`.

**Step 3: Add Wallos journal check**

Add a `journalctl` call for `kiran-wallos-litestream.service`.

### Task 4: Document backup behavior in Wallos stack README

**Files:**
- Modify: `stacks/wallos/README.md`

**Step 1: Add Backups section**

Document that Wallos uses Litestream with Garage S3 and that orchestration is managed by `provision/roles/litestream-backup`.

**Step 2: Confirm bucket naming**

Mention `wallos-backups` explicitly so operations match infra config.

### Task 5: Verify end-to-end behavior

**Files:**
- No direct file changes

**Step 1: Run repo verification**

Run: `task verify`

Expected: pass.

**Step 2: Apply provisioning**

Run: `task provision`

Expected: creates/enables `kiran-wallos-litestream.service` and `kiran-wallos-litestream-check.timer`.

**Step 3: Validate backup services**

Run: `task litestream:health`

Expected: Wallos service is active; timer listed; recent journal entries present.
