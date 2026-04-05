# Music Stack

Compose file: `stacks/music/compose.yaml`

## In Komodo

1. Create or open the `music` stack.
2. Set compose path to `stacks/music/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<NAVIDROME_HOST>`.

## Stack environment variables

- `NAVIDROME_HOST` (required): public hostname. Example: `music.fewa.app`.
- `LIDARR_HOST` (required): public hostname. Example: `lidarr.fewa.app`.
- `FEISHIN_HOST` (required): public hostname. Example: `feishin.fewa.app`.
- `TZ` (optional): timezone. Default: `UTC`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `PUID` (optional): user ID for file permissions. Default: `1000`.
- `PGID` (optional): group ID for file permissions. Default: `1000`.

## Volume mappings

### Navidrome
- `/config`: database, users, settings, logs.
- `/music`: music library (shared with Lidarr).

### Lidarr
- `/config`: database, settings, logs.
- `/music`: music library (shared with Navidrome).
- `/downloads`: download folder for new music.

### Feishin
- No persistent volumes (stateless client).

## Notes

- Navidrome, Lidarr, and Feishin share the same `/music` volume.
- Lidarr downloads music to `/downloads`, then it's available in Navidrome/Feishin.
- All services use SQLite internally (Navidrome and Lidarr store in config volumes).
- Navidrome runs on port 4533, Lidarr on 8686, Feishin on 9180.
- Feishin connects to Navidrome via Subsonic API for a modern Spotify-like interface.