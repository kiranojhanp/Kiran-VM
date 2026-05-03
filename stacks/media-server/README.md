# Media Server Stack

Plex media server with Sonarr, Radarr, and Prowlarr for automated TV/movie management.

## Architecture

```
Torbox → Decypharr (media-stack) → mounts at /mnt/decypharr
                                    ↓
Prowlarr (indexer) → Sonarr (TV) ──→ /mnt/decypharr/tv
                     → Radarr (Movies) → /mnt/decypharr/movies
                                    ↓
                                Plex (serves to devices)
```

## Quick Start

1. Create `media-server` stack in Komodo
2. Set compose path to `stacks/media-server/compose.yaml`
3. Copy `.env.sample` to `.env` and fill in values
4. Add stack environment variables:
   - `SONARR_HOST` = `sonarr.fewa.app`
   - `RADARR_HOST` = `radarr.fewa.app`
   - `PROWLARR_HOST` = `prowlarr.fewa.app`
   - `SHARED_DOCKER_NETWORK` = `internal-network`
   - `PLEX_CLAIM` = (from https://www.plex.tv/claim/ - expires in 4 min)
5. Deploy

## Required Variables

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `SONARR_HOST` | Public hostname for Sonarr | `sonarr.fewa.app` |
| `RADARR_HOST` | Public hostname for Radarr | `radarr.fewa.app` |
| `PROWLARR_HOST` | Public hostname for Prowlarr | `prowlarr.fewa.app` |
| `PLEX_CLAIM` | Plex claim token (expires 4 min) | (from https://plex.tv/claim) |

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| Plex | `http://<server-ip>:32400/web` | Media streaming server |
| Sonarr | `https://sonarr.fewa.app` | TV show automation |
| Radarr | `https://radarr.fewa.app` | Movie automation |
| Prowlarr | `https://prowlarr.fewa.app` | Indexer manager |

## Configuration Steps

### 1. Prowlarr (Indexer Manager)
- Go to `https://prowlarr.fewa.app`
- Add indexers: Settings → Indexers → Add Indexer
- Connect to Sonarr: Settings → Apps → Add Application → Sonarr
  - Host: `http://sonarr:8989`
  - API Key: (from Sonarr → Settings → General → Security)
- Connect to Radarr: Settings → Apps → Add Application → Radarr
  - Host: `http://radarr:7878`
  - API Key: (from Radarr → Settings → General → Security)

### 2. Sonarr (TV Shows)
- Go to `https://sonarr.fewa.app`
- Add Decypharr as download client: Settings → Download Clients → + → qBittorrent
  - Host: `decypharr`
  - Port: `8282`
  - Username: `http://sonarr:8989`
  - Password: (Sonarr API token)
  - Category: `sonarr`
- Add root folder: `/tv`
- Add shows → Sonarr handles the rest

### 3. Radarr (Movies)
- Go to `https://radarr.fewa.app`
- Add Decypharr as download client: Settings → Download Clients → + → qBittorrent
  - Host: `decypharr`
  - Port: `8282`
  - Username: `http://radarr:7878`
  - Password: (Radarr API token)
  - Category: `radarr`
- Add root folder: `/movies`
- Add movies → Radarr handles the rest

### 4. Plex
- Go to `http://<server-ip>:32400/web` (Plex uses host networking)
- Add libraries:
  - TV Shows → `/tv`
  - Movies → `/movies`
- Plex will auto-scan when Sonarr/Radarr imports files

## Notes

- Plex uses `network_mode: host` for local network discovery and DLNA
- Sonarr/Radarr/Decypharr must all see the same mount path (`/mnt/decypharr`)
- Decypharr mounts Torbox content via DFS to `/mnt/decypharr`
- Prowlarr syncs indexers to both Sonarr and Radarr automatically
- Media files are read-only to Plex (Decypharr manages the mount)
