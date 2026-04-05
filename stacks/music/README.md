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

## Notes

- Navidrome and Lidarr share the same `/music` volume - music downloaded by Lidarr is immediately available in Navidrome.
- Both services use SQLite internally (stored in their respective config volumes).
- Navidrome runs on port 4533, Lidarr on port 8686.
- Navidrome supports Subsonic API, compatible with many music clients (including Feishin, Symfonium, DSub).