# Actual Budget Stack

Compose file: `stacks/actual/compose.yaml`

## In Komodo

1. Create or open the `actual` stack.
2. Set compose path to `stacks/actual/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<ACTUAL_HOST>`.

## Stack environment variables

- `ACTUAL_HOST` (required): public hostname. Example: `actual.fewa.app`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

Do not set `ACTUAL_PORT` in Komodo. It is fixed to `5006` in compose.

### OpenID / authentik SSO

To enable authentik SSO:

1. **In authentik**: Create OAuth2/OIDC provider with:
   - Redirect URI (Strict): `https://actual.fewa.app/openid/callback`
   - Signing Key: select any (Actual only supports RS256)
2. **In Komodo**, set these variables:
   - `ACTUAL_OPENID_DISCOVERY_URL`: `https://authentik.fewa.app/application/o/<slug>/`
   - `ACTUAL_OPENID_CLIENT_ID`: from authentik
   - `ACTUAL_OPENID_CLIENT_SECRET`: from authentik

**Important:** Users must be manually created in Actual Budget first (go to Server online → User Directory) before SSO login will work.

## Security

This stack includes Docker security hardening:

- **Read-only root filesystem**: Prevents container from writing to root filesystem
- **No new privileges**: Prevents privilege escalation attacks
- **Dropped all capabilities**: Removes all Linux capabilities (`cap_drop: ALL`)
- **Memory limits**: `mem_limit` and `memswap_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit: 100` prevents fork bombs
- **Tmpfs mount**: `/tmp` mounted as tmpfs where write access needed
