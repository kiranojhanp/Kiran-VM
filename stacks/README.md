# stacks

Traefik templates and generated files live here.

## Quickstart

If you change routing or domain defaults:

```bash
task sync
task update
task verify
```

That is all most users need.

## What is managed here

- `stacks/traefik/*.tmpl.yml` - templates
- `stacks/traefik/compose.yaml` - generated
- `stacks/traefik/traefik.yml` - generated
- `stacks/traefik/dynamic.yml` - generated

Traefik is deployed by Ansible during `task push` / `task update`.

## Secret used here

- `cloudflare_api_token` from `provision/secrets.yml`
