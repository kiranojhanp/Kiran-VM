# finance-stack

This directory groups finance and budgeting app stacks deployed from Komodo.

## Stacks in this group

- [Yuvomi](yuvomi/README.md): self-hosted family planner / household finance & budgeting.

## What to do in Komodo

Use the same flow as any other stack:

1. Create the stack in Komodo (or open the existing one).
2. Set the run directory to `stacks/finance-stack/<stack-name>`.
3. Set variables in the stack Environment section.
4. Deploy (or Redeploy).

## Where each variable belongs

- Komodo stack environment: app runtime values used in `stacks/*/compose.yaml`.
- `provision/secrets.yml` (ansible-vault): platform secrets (`cloudflare_api_token`, `komodo_*`, shared DB/Redis passwords).
- Pulumi config (`infra` stack): OCI and infrastructure values (`oci:*`, `kiran-vm-infra:*`).

Komodo platform variables are not set per app stack. Provisioning renders them from `provision/secrets.yml` and `provision/group_vars/all.yml` into `/opt/komodo/.env` (for example: `KOMODO_WEBHOOK_SECRET`, `KOMODO_JWT_SECRET`, `KOMODO_INIT_ADMIN_USERNAME`, `KOMODO_INIT_ADMIN_PASSWORD`, `PERIPHERY_CORE_PUBLIC_KEYS`).

If a compose file references `${...}`, set it in that stack's Komodo Environment unless that stack README says otherwise.