# Media Server Stack

Plex media server with Sonarr (TV), Radarr (Movies), and Decypharr (Torbox debrid manager with DFS mount).

## Architecture

```
Torbox → Decypharr (mounts at /mnt/decypharr via DFS)
                              ↓
                    Sonarr (/tv) + Radarr (/movies)
                              ↓
                           Plex (serves to devices)
```

## Quick Start

1. Create `media-server` stack in Komodo
2. Set compose path to `stacks/media-server/compose.yaml`
3. Copy `.env.sample` to `.env` and fill in values
4. Add stack environment variables:
   - `DECYPHARR_HOST` = `decypharr.fewa.app`
   - `SONARR_HOST` = `sonarr.fewa.app`
   - `RADARR_HOST` = `radarr.fewa.app`
   - `SHARED_DOCKER_NETWORK` = `internal-network`
   - `SHARED_INFRA_NETWORK` = `infra_net`
   - `PLEX_CLAIM` = (from https://www.plex.tv/claim/ - expires in 4 min)
   - `TORBOX_API_KEY` = (from Torbox dashboard)
5. Deploy

## Required Variables

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `DECYPHARR_HOST` | Public hostname for Decypharr | `decypharr.fewa.app` |
| `SONARR_HOST` | Public hostname for Sonarr | `sonarr.fewa.app` |
| `RADARR_HOST` | Public hostname for Radarr | `radarr.fewa.app` |
| `PLEX_CLAIM` | Plex claim token (expires 4 min) | (from https://plex.tv/claim) |
| `TORBOX_API_KEY` | Torbox API key | (from Torbox dashboard) |

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| Decypharr | `https://decypharr.fewa.app` | Torbox debrid manager + DFS mount |
| Plex | `http://<server-ip>:32400/web` | Media streaming server |
| Sonarr | `https://sonarr.fewa.app` | TV show automation |
| Radarr | `https://radarr.fewa.app` | Movie automation |

## Configuration Steps

### 1. Decypharr (Torbox + Mount)
- Go to `https://decypharr.fewa.app`
- **Mount Type**: DFS, Mount Path: `/mnt/decypharr`, Cache Dir: `/cache/dfs`
- **Debrid**: Add Torbox API key
- This mounts your Torbox content as a local filesystem at `/mnt/decypharr`

### 2. Sonarr (TV Shows)
- Go to `https://sonarr.fewa.app`
- **Download Client**: Settings → Download Clients → + → qBittorrent
  - Host: `decypharr`
  - Port: `8282`
  - Username: `http://sonarr:8989`
  - Password: (Sonarr API token from Settings → General)
  - Category: `sonarr`
- **Root Folder**: `/tv` (points to `/mnt/decypharr/tv`)
- Add shows → Sonarr handles the rest

### 3. Radarr (Movies)
- Go to `https://radarr.fewa.app`
- **Download Client**: Same as Sonarr but:
  - Username: `http://radarr:7878`
  - Password: (Radarr API token)
  - Category: `radarr`
- **Root Folder**: `/movies` (points to `/mnt/decypharr/movies`)
- Add movies → Radarr handles the rest

### 4. Plex
- Go to `http://<server-ip>:32400/web` (Plex uses host networking)
- Claim server with your Plex account
- **Add Libraries**:
  - TV Shows → Folder: `/tv`
  - Movies → Folder: `/movies`
- Plex auto-scans when Sonarr/Radarr imports files

## Notes

- Plex uses `network_mode: host` for local network discovery and DLNA
- Sonarr/Radarr/Decypharr must all see the same mount path (`/mnt/decypharr`)
- Decypharr mounts Torbox content via DFS to `/mnt/decypharr`
- No Prowlarr needed — Decypharr uses Torbox's built-in search
- Media files are read-only to Plex (Decypharr manages the mount)
