# stacks/

Docker Compose stacks managed by [Komodo](https://komo.do).

This repo officially curates one managed stack: `traefik`.

Komodo itself is provisioned by Ansible (`provision/roles/komodo`) as base control plane, not as a curated `stacks/` compose file.

Everything else should be added as your own Komodo-managed stacks.

## Supported stack

- `stacks/traefik/compose.yaml`
- `stacks/traefik/traefik.yml`
- `stacks/traefik/dynamic.yml`
- `stacks/traefik/*.tmpl.yml|yaml` (templates)

The concrete `compose.yaml`, `traefik.yml`, and `dynamic.yml` files are generated from templates by `task sync` using `Taskfile.yml` vars.

`traefik` runs on a shared external Docker network (`internal-network` by default) so app stacks can be routed by service name.

The network is created by Ansible during `task provision` using `Taskfile.yml` variable `SHARED_DOCKER_NETWORK`.

Default:

```bash
SHARED_DOCKER_NETWORK=internal-network
```

Any app stack you want to expose should join `SHARED_DOCKER_NETWORK` and provide a stable alias.

## Deploying traefik

**Automatically** - push changes under `stacks/traefik/**` to `main`. GitHub Actions triggers the Komodo traefik procedure.

**Manually** - Komodo UI -> Stacks -> traefik -> Deploy.

## Secrets

Runtime secrets live in Komodo (Settings -> Variables), referenced in compose as `[[SECRET_NAME]]`.

Required for traefik:

- `CLOUDFLARE_API_TOKEN` for DNS-01 certificate issuance.

## Routing updates

Edit `Taskfile.yml` defaults for domain/cert settings, then run `task sync` to regenerate Traefik configs. For structural routing changes, update `stacks/traefik/dynamic.tmpl.yml` and run `task sync`.

For this repo's default routes (derived from Taskfile vars):

- `${KOMODO_SUBDOMAIN_LABEL}.${DOMAIN_NAME_DEFAULT}` routes to `http://komodo:9120` on `SHARED_DOCKER_NETWORK`.
- `${DOMAIN_NAME_DEFAULT}` routes to the built-in `fewa-site` container.

Pulumi-managed DNS subdomains are controlled by `DNS_SUBDOMAIN_LABELS` in `Taskfile.yml`.

## Troubleshooting

**Certificate not issued** - Cloudflare API token needs `Zone -> DNS -> Edit` for the target zone.

**502 Bad Gateway** - upstream container is not running, not on `SHARED_DOCKER_NETWORK`, or missing the expected service alias.

**Webhook not firing** - check GitHub Actions logs and verify `KOMODO_WEBHOOK_TRAEFIK` is set.
