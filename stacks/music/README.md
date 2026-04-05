# Music Stack

Compose file: `stacks/music/compose.yaml`

## In Komodo

1. Create or open the `music` stack.
2. Set compose path to `stacks/music/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<FEISHIN_HOST>`.

## Prerequisites

Before deploying, create the music folder on your server:
```bash
sudo mkdir -p /opt/music
sudo chown -R 1000:1000 /opt/music
```

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

### Host folder: `/opt/music`
The music library lives on the host at `/opt/music`. All music services access this folder:
- **Navidrome**: `/opt/music` → `/music` (read-only)
- **Lidarr**: `/opt/music` → `/music` (read-write)
- **slskd**: `/opt/music` → `/data` (read-only, for sharing on Soulseek)

### Other volumes
- Navidrome: `/config` - database, settings
- Lidarr: `/config` - database, settings; `/downloads` - download folder
- Prowlarr: `/config` - indexer configs, settings
- slskd: `/app` - config; `/downloads`, `/incomplete` - download folders
- Soularr: `/data` - config

## Configuration

### Lidarr Setup
1. Go to Lidarr → Settings → Media Management
2. Add root folder: `/music`
3. Go to Settings → Indexers
4. Add Prowlarr as an indexer (Add via Prowlarr)
5. Go to Settings → Download Clients
6. Add Soularr as download client
7. Add artists to monitor

### Prowlarr → Lidarr Sync
1. Go to Prowlarr (`prowlarr.fewa.app`) → Settings → Apps
2. Add Application → Select Lidarr
3. Configure:
   - Prowlarr Server: `http://prowlarr:9696`
   - Lidarr Server: `http://lidarr:8686`
   - API Key: Get from Lidarr → Settings → General
4. Save - indexers will sync to Lidarr

### slskd Setup
1. Go to `https://slskd.fewa.app`
2. Login: `slskd` / `slskd` (default)
3. Go to System → Options → Edit
4. Configure:
   ```yaml
   directories:
     incomplete: /incomplete
     downloads: /downloads
   shares:
     directories:
       - /data/music
   ```
5. Set web credentials (not SoulSeek)
6. Set your SoulSeek username/password
7. Click "Disconnected" to connect to SoulSeek network

## Notes

- Music folder is bind-mounted from host: `/opt/music`
- Lidarr downloads go to `/downloads` (Docker volume, not host)
- Soularr/slskd downloads go to their volumes
- Feishin connects to Navidrome via Subsonic API for the best UI experience
- Prowlarr manages indexers for all *arr applications