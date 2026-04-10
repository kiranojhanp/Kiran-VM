# Vikunja Stack

Compose file: `stacks/vikunja/compose.yaml`

## In Komodo

1. Create or open the `vikunja` stack.
2. Set compose path to `stacks/vikunja/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<VIKUNJA_HOST>`.

## Stack environment variables

- `VIKUNJA_HOST` (required): public hostname. Example: `vikunja.fewa.app`.
- `VIKUNJA_JWT_SECRET` (required): strong random secret for JWT.
- `VIKUNJA_DB_NAME` (required): database name.
- `VIKUNJA_DB_USER` (required): database user.
- `VIKUNJA_DB_PASSWORD` (required): database password.
- `SHARED_POSTGRES_HOST` (optional): shared Postgres host. Default: `postgres`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `SHARED_INFRA_NETWORK` (optional): shared infra network. Default: `infra_net`.

### OpenID / authentik SSO

To enable authentik SSO, set these variables:

- `VIKUNJA_AUTH_OPENID_AUTHURL` (required): OpenID provider URL. Example: `https://authentik.fewa.app/application/o/<slug>/`
- `VIKUNJA_AUTH_OPENID_CLIENTID` (required): OAuth2 Client ID from authentik.
- `VIKUNJA_AUTH_OPENID_CLIENTSECRET` (required): OAuth2 Client Secret from authentik.
- `VIKUNJA_AUTH_LOCAL_ENABLED` (optional): Set to `false` to disable local login. Default: `true`.

**Note:** In authentik, set the Redirect URI to `https://vikunja.fewa.app/auth/openid/authentik`.

## Security

This stack includes Docker security hardening:

- **Read-only root filesystem**: Prevents container from writing to root filesystem
- **No new privileges**: Prevents privilege escalation attacks
- **Dropped all capabilities**: Removes all Linux capabilities (`cap_drop: ALL`)
- **Memory limits**: `mem_limit` and `memswap_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit: 100` prevents fork bombs
