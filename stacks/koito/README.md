# Koito Stack

Compose file: `stacks/koito/compose.yaml`

Koito is a themeable, ListenBrainz-compatible scrobbler. Any client that can
scrobble to a custom ListenBrainz URL (Navidrome, Feishin, Symfonium, Web
Scrobbler, etc.) can scrobble to it.

## In Komodo

1. Create or open the `koito` stack.
2. Set compose path to `stacks/koito/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<KOITO_HOST>`.

## Stack environment variables

- `KOITO_HOST` (required): public hostname. Example: `koito.fewa.app`.
- `KOITO_DEFAULT_PASSWORD` (required): password for the initial admin user.
  Only used on the very first startup — changing it later has no effect.
  Store it as a Komodo secret rather than plain text in the stack environment.
- `KOITO_DEFAULT_USERNAME` (optional): initial admin username. Default: `admin`.
- `KOITO_LOGIN_GATE` (optional): when `true`, statistics require login.
  Default: `true` (personal listening data should not be public).
- `KOITO_LOG_LEVEL` (optional): `debug`, `info`, `warn`, `error`, or `fatal`.
  Default: `info`.
- `KOITO_ENABLE_LBZ_RELAY` (optional): relay incoming listens to another
  ListenBrainz-compatible server. Default: `false`.
- `KOITO_LBZ_RELAY_URL` (required if relay is enabled): full ListenBrainz
  endpoint, for example `https://api.listenbrainz.org/1`.
- `KOITO_LBZ_RELAY_TOKEN` (required if relay is enabled): token for the relay
  target.
- `KOITO_SUBSONIC_URL` (optional): Subsonic-compatible server URL (for example
  Navidrome) used to fetch artwork. Must be set together with
  `KOITO_SUBSONIC_PARAMS`.
- `KOITO_SUBSONIC_PARAMS` (optional): `u=...&t=...&s=...` auth parameters from
  your Subsonic server. Koito fails to start if these are invalid.
- `KOITO_LASTFM_API_KEY` (optional): Last.fm API key for additional artwork.
- `TZ` (optional): timezone. Default: `UTC`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default:
  `internal-network`.

## Connecting scrobblers

1. Log in with the initial credentials and change the password.
2. Open Settings → API Keys and copy the generated key.
3. Point the client at:
   - `https://<KOITO_HOST>/apis/listenbrainz/1` (or `/apis/listenbrainz` for
     clients that expect the shorter form)
   - Token: the API key from the UI.

For Navidrome, see <https://koito.io/quickstart/navidrome/>. To try Koito
without abandoning an existing scrobbler, enable the relay variables above.

## Notes

- SQLite only (upstream dropped PostgreSQL in v0.2.1). The database, image
  cache, and import folder live under `/etc/koito` in the `koito_data` volume.
- First startup creates the admin user. `KOITO_DEFAULT_*` is ignored on later
  starts, so rotating the password is done in the UI.
- Upstream considers the project unstable; the image is pinned to a release
  tag rather than `latest`.
- Import from Maloja, ListenBrainz, Last.fm, or Spotify via the UI; see
  <https://koito.io/guides/importing/>.

## Backups

Koito uses Litestream for continuous SQLite replication to Garage S3. This is
managed via Ansible in `provision/roles/litestream-backup` with service name
`koito` and bucket `koito-backups`. The database is `koito.db` (WAL mode) in
the `koito_koito_data` volume.

Create the bucket once and allow the shared S3 key (same key used by the other
Litestream services):

```bash
docker exec garage garage bucket create koito-backups
docker exec garage garage bucket allow koito-backups --read --write --key <garage_access_key_id>
```

## Security

This stack includes Docker security hardening:

- **No new privileges**: Prevents privilege escalation attacks
- **Dropped all capabilities**: Removes all Linux capabilities (`cap_drop: ALL`)
- **Memory limits**: `mem_limit` and `memswap_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit: 200` prevents fork bombs
- **Pinned image tag**: avoids surprise upgrades from upstream's unstable branch

A read-only root filesystem is intentionally not set because libvips may need
scratch space; the service only mounts writable state at `/etc/koito`.
