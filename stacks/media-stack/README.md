# Media Stack

Self-hosted AIOMetadata service for Stremio metadata caching with poster caching via nginx.

## Quick Start

1. Create/open the `media-stack` in Komodo
2. Set compose path to `stacks/media-stack/compose.yaml`
3. Copy `.env.sample` to `.env` and fill in values
4. Add stack environment variables:
   - `AIOMETADATA_HOST` = `aiometadata.fewa.app`
   - `SHARED_DOCKER_NETWORK` = `internal-network`
   - `SHARED_INFRA_NETWORK` = `infra_net`
   - `REDIS_HOST_SHARED` = (from Komodo secrets, format: `redis://:password@redis:6379`)
5. Deploy

## Required Variables

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `AIOMETADATA_HOST` | Public hostname for AIOMetadata | `aiometadata.fewa.app` |
| `REDIS_HOST_SHARED` | Redis connection URL | `redis://:password@redis:6379` |

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| AIOMetadata | `https://aiometadata.fewa.app` | Metadata cache for Stremio |
| Poster Cache | `https://poster-cache.fewa.app` | Nginx-based poster image cache |

## Notes

- This stack replaces the old `aiostreams` stack which included AIOStreams, Jackett, WARP, and MediaFlow Proxy
- You can use AIOMetadata with Torrentio addon directly in Stremio for a simpler setup
- Poster cache uses nginx to cache poster images for 30 days
