# Media Stack

Self-hosted Stremio/Nuvio addons: AIOMetadata metadata caching, poster cache, and the Live Sports addon.

## Quick Start

1. Create/open the `media-stack` in Komodo
2. Set compose path to `stacks/media-stack/compose.yaml`
3. Copy `.env.sample` to `.env` and fill in values
4. Add stack environment variables:
   - `AIOMETADATA_HOST` = `aiometadata.fewa.app`
   - `LIVE_SPORTS_HOST` = `live-sports.fewa.app`
   - `SHARED_DOCKER_NETWORK` = `internal-network`
   - `SHARED_INFRA_NETWORK` = `infra_net`
   - `REDIS_HOST_SHARED` = (from Komodo secrets, format: `redis://:password@redis:6379`)
5. Deploy

## Required Variables

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `AIOMETADATA_HOST` | Public hostname for AIOMetadata | `aiometadata.fewa.app` |
| `LIVE_SPORTS_HOST` | Public hostname for Live Sports | `live-sports.fewa.app` |
| `REDIS_HOST_SHARED` | Redis connection URL (AIOMetadata only) | `redis://:password@redis:6379` |

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| AIOMetadata | `https://aiometadata.fewa.app` | Metadata cache for Stremio |
| Poster Cache | `https://poster-cache.fewa.app` | Nginx-based poster image cache |
| Live Sports | `https://live-sports.fewa.app` | Live sports addon (scrapes/aggregates public fixtures and streams) |

## Live Sports setup

- Add `https://live-sports.fewa.app/manifest.json` as an addon in Nuvio / Stremio.
- Open `https://live-sports.fewa.app/configure` to filter sports categories, providers, timezone, and favorite teams.
- **Built from source** (`ghcr.io/rajhodedara/live-sport-plugin:latest` is published amd64-only, and this host is ARM64 Ampere with no QEMU emulation). The service uses `build.context` pointed at the upstream git repo + `pull_policy: never`; Deploy builds a native arm64 image (~5–10 min on first deploy, afterwards reused).
- **Stateless:** uses no Postgres/Redis (persistent prefs live in the addon config URL, catalogs are held in memory), so it joins only the `shared` network — no `infra` network, no shared DB access.

## Notes

- This stack replaces the old `aiostreams` stack which included AIOStreams, Jackett, WARP, and MediaFlow Proxy
- You can use AIOMetadata with Torrentio addon directly in Stremio for a simpler setup
- Poster cache uses nginx to cache poster images for 30 days
