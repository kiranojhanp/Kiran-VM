# Music Stack

Compose file: `stacks/music/compose.yaml`

## In Komodo

1. Create or open the `music` stack.
2. Set compose path to `stacks/music/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<FEISHIN_HOST>`.

## Stack environment variables

- `NAVIDROME_HOST` (optional): public hostname. Default: `navidrome.fewa.app`.
- `LIDARR_HOST` (optional): public hostname. Default: `lidarr.fewa.app`.
- `FEISHIN_HOST` (optional): public hostname. Default: `music.fewa.app`.
- `PROWLARR_HOST` (optional): public hostname. Default: `prowlarr.fewa.app`.
- `SLSKD_HOST` (optional): public hostname. Default: `slskd.fewa.app`.
- `SOULARR_HOST` (optional): public hostname. Default: `soularr.fewa.app`.
- `TZ` (optional): timezone. Default: `UTC`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `PUID` (optional): user ID for file permissions. Default: `1000`.
- `PGID` (optional): group ID for file permissions. Default: `1000`.

## Services

| Service   | URL                   | Port | Purpose                              |
| --------- | --------------------- | ---- | ------------------------------------ |
| Feishin   | music.fewa.app        | 9180 | Spotify-like UI for browsing/playing |
| Navidrome | navidrome.fewa.app    | 4533 | Music server backend                 |
| Lidarr    | lidarr.fewa.app       | 8686 | Auto-download music for artists      |
| Prowlarr  | prowlarr.fewa.app     | 9696 | Indexer manager                      |
| slskd     | slskd.fewa.app        | 5030 | Soulseek daemon (backend)            |
| Soularr   | soularr.fewa.app      | 5055 | Soulseek client (UI)                 |

## Volume mappings

### Navidrome
- `/config`: database, users, settings, logs.
- `/music`: music library (shared with Lidarr, exposed to slskd).

### Lidarr
- `/config`: database, settings, logs.
- `/music`: music library (shared with Navidrome).
- `/downloads`: download folder for new music.

### Feishin
- No persistent volumes (stateless client).

### Prowlarr
- `/config`: database, indexer configs, settings.

### slskd
- `/app`: configuration and data.
- `/downloads`: completed downloads (shared with Soularr).
- `/incomplete`: incomplete downloads.
- `/data`: read-only access to music library for sharing.

### Soularr
- `/data`: configuration and data.
- `/downloads`: download queue (shared with slskd).
- `/incomplete`: incomplete downloads.

## Configuration

### Lidarr Setup
1. Go to Lidarr → Settings → Indexers
2. Add Prowlarr as an indexer (Add via Prowlarr)
3. Go to Settings → Download Clients
4. Add Soularr as download client
5. Add artists to monitor

### Soularr/slskd Setup
1. Go to `https://slskd.fewa.app` to configure slskd
2. Go to `https://soularr.fewa.app` to use Soulseek client
3. Configure username/password in slskd to connect to Soulseek network

## Notes

- All services share the same music library via Docker volumes.
- Lidarr searches via Prowlarr indexers and downloads via Soularr.
- Feishin connects to Navidrome via Subsonic API for the best UI experience.
- Prowlarr manages indexers for all *arr applications.