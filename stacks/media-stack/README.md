# Media Stack

Self-hosted AIOMetadata service for Stremio metadata caching with poster caching via nginx, plus Decypharr for debrid media management.

## Quick Start

1. Create/open the `media-stack` in Komodo
2. Set compose path to `stacks/media-stack/compose.yaml`
3. Copy `.env.sample` to `.env` and fill in values
4. Add stack environment variables:
   - `AIOMETADATA_HOST` = `aiometadata.fewa.app`
   - `DECYPHARR_HOST` = `decypharr.fewa.app`
   - `SHARED_DOCKER_NETWORK` = `internal-network`
   - `SHARED_INFRA_NETWORK` = `infra_net`
   - `REDIS_HOST_SHARED` = (from Komodo secrets, format: `redis://:password@redis:6379`)
5. Deploy

## Required Variables

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `AIOMETADATA_HOST` | Public hostname for AIOMetadata | `aiometadata.fewa.app` |
| `DECYPHARR_HOST` | Public hostname for Decypharr | `decypharr.fewa.app` |
| `REDIS_HOST_SHARED` | Redis connection URL | `redis://:password@redis:6379` |
| `REAL_DEBRID_API_KEY` | Real Debrid API key | (from https://real-debrid.com/apitoken) |
| `SONARR_TOKEN` | Sonarr API token | (from Sonarr -> Settings -> General) |
| `RADARR_TOKEN` | Radarr API token | (from Radarr -> Settings -> General) |

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| AIOMetadata | `https://aiometadata.fewa.app` | Metadata cache for Stremio |
| Decypharr | `https://decypharr.fewa.app` | Debrid media manager (mounts + Arr integration) |
| Poster Cache | `https://poster-cache.fewa.app` | Nginx-based poster image cache |

## Configuration

### AIOMetadata .env

Copy `.env.sample` to `.env` and configure:

```bash
# TMDB API Key (get from https://www.themoviedb.org/settings/api)
TMDB_API=your_tmdb_api_key

# TVDB API Key (get from https://thetvdb.com/)
TVDB_API_KEY=your_tvdb_api_key

# Redis URL (uses REDIS_HOST_SHARED via compose)
# REDIS_URL is set in compose via REDIS_HOST_SHARED

# Database (SQLite is default, no config needed)
# DATABASE_URI=sqlite://addon/data/db.sqlite

# Optional: Enable cache warming for faster first-load
# ENABLE_CACHE_WARMING=true
```

### Decypharr Config

Copy `decypharr-config.json.sample` to `decypharr-config.json` and configure:

```json
{
  "mount": {
    "type": "dfs",
    "mount_path": "/mnt/decypharr",
    "dfs": {
      "cache_dir": "/cache/dfs",
      "chunk_size": "10MB",
      "disk_cache_size": "50GB",
      "cache_expiry": "24h",
      "daemon_timeout": "30m",
      "uid": 1000,
      "gid": 1000,
      "allow_other": true
    }
  },
  "debrids": [
    {
      "provider": "realdebrid",
      "name": "Real Debrid",
      "api_key": "YOUR_REAL_DEBRID_API_KEY"
    }
  ],
  "arrs": [
    {
      "name": "Sonarr",
      "host": "http://sonarr:8989",
      "token": "YOUR_SONARR_TOKEN",
      "download_action": "symlink"
    },
    {
      "name": "Radarr",
      "host": "http://radarr:7878",
      "token": "YOUR_RADARR_TOKEN",
      "download_action": "symlink"
    }
  ]
}
```

**Sonarr/Radarr Setup:** In Sonarr/Radarr, add Decypharr as a **qBittorrent** download client:
- Host: `decypharr` (or container IP)
- Port: `8282`
- Username: Arr's host (e.g. `http://sonarr:8989`)
- Password: Arr's API token
- Category: `sonarr` / `radarr`

## Notes

- This stack replaces the old `aiostreams` stack which included AIOStreams, Jackett, WARP, and MediaFlow Proxy
- You can use AIOMetadata with Torrentio addon directly in Stremio for a simpler setup
- Poster cache uses nginx to cache poster images for 30 days
- Decypharr mounts debrid content as a local filesystem (DFS) for Plex/Jellyfin
- Decypharr requires FUSE (`/dev/fuse`) and `SYS_ADMIN` capability on the host
