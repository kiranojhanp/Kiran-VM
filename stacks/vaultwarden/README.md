# Vaultwarden Stack

Compose file: `stacks/vaultwarden/compose.yaml`

## In Komodo

1. Create or open the `vaultwarden` stack.
2. Set compose path to `stacks/vaultwarden/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<VAULTWARDEN_HOST>`.

## Stack environment variables

- `VAULTWARDEN_HOST` (required): public hostname. Example: `vaultwarden.fewa.app`.
- `VAULTWARDEN_SIGNUPS_ALLOWED` (optional): allow signup (`true` or `false`). Default: `false`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

### SSO / authentik

To enable authentik SSO:

1. **In authentik**: Create OAuth2/OIDC provider with redirect URI: `https://vaultwarden.fewa.app/identity/connect/oidc-signin`
2. **Custom scope mapping** (required): Create scope mapping with expression:
   ```
   return {
       "email": request.user.email,
       "email_verified": True
   }
   ```
3. **In Komodo**, set these variables:
   - `VAULTWARDEN_SSO_AUTHORITY`: `https://authentik.fewa.app/application/o/<slug>/`
   - `VAULTWARDEN_SSO_CLIENT_ID`: from authentik
   - `VAULTWARDEN_SSO_CLIENT_SECRET`: from authentik
   - `VAULTWARDEN_SSO_ONLY` (optional): set to `true` to disable email+password login
   - `DOMAIN` (required): must match your VAULTWARDEN_HOST. Example: `https://vaultwarden.fewa.app`

## Backups

Vaultwarden uses Litestream for continuous SQLite replication to Garage S3. This is managed via Ansible in `provision/roles/vaultwarden-litestream`. Enable by setting `vaultwarden_litestream_enabled: true` in `group_vars/all.yml` and adding credentials to `secrets.yml`.
