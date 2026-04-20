# AIOStreams Stack

Self-hosted Stremio addon aggregator with Jackett for custom torrent indexers.

## Important Hosting Warnings

| Warning | Details |
| ------- | ------- |
| **No Free Tiers** | HuggingFace/Render free tiers are NOT suitable for media streaming. You WILL get kicked due to bandwidth usage. |
| **Use VPS/Home** | Use a VPS (Oracle, Hetzner) or home server instead |
| **HTTPS Required** | Stremio only connects to HTTPS endpoints. Port 443 must be open. |

## Quick Start

1. Create/open the `aiostreams` stack in Komodo
2. Set compose path to `stacks/aiostreams/compose.yaml`
3. Copy `.env.sample` to `.env` and fill in values
4. Add stack environment variables:
   - `AIOSTREAMS_HOST` = `aiostreams.fewa.app`
   - `JACKETT_HOST` = `jackett.fewa.app` (optional)
   - `AIOMETADATA_HOST` = `aiometadata.fewa.app`
   - `MEDIAFLOW_HOST` = `mediaflow.fewa.app` (optional, for proxy services)
   - `SHARED_DOCKER_NETWORK` = `internal-network`
   - `SHARED_INFRA_NETWORK` = `infra_net`
   - `REDIS_HOST_SHARED` = (from Komodo secrets, format: `redis://:password@redis:6379`)
5. Deploy

## Required Variables

| Variable | Description | Example |
| -------- | ----------- | -------- |
| `AIOSTREAMS_HOST` | Public hostname | `aiostreams.fewa.app` |
| `SECRET_KEY` | 64-char hex (in .env) | `openssl rand -hex 32` |

## Setup

### 1. Configure .env

Copy `.env.sample` to `.env` and fill in:

```bash
# Generate secret key
openssl rand -hex 32

# Add TorBox API key from TorBox dashboard
TORBOX_API_KEY=your_api_key_here
```

### 2. Configure Jackett

1. Open `https://jackett.fewa.app`
2. Add torrent indexers (1337x, RARBG, YTS, etc.)
3. Note the API key for AIOStreams

### 3. Configure AIOStreams

1. Open `https://aiostreams.fewa.app/stremio/configure`
2. Add your TorBox API key
3. Add Jackett as a source using the API key from step 2
4. Configure your debrid service

## Services

| Service | URL | Purpose | Profile |
|---------|-----|---------|---------|
| AIOStreams | `https://aiostreams.fewa.app` | Stremio addon | default |
| Jackett | `https://jackett.fewa.app` | Torrent indexers | default |
| AIOMetadata | `https://aiometadata.fewa.app` | Metadata cache | default |
| WARP | `internal:1080` | Cloudflare WARP for IP rotation | proxy |
| MediaFlow Proxy | `https://mediaflow.fewa.app` | Proxy for Torrentio/DRM | proxy |

### Proxy Services (Optional)

Enable with: `docker compose --profile proxy up`

- **WARP**: Cloudflare WARP to rotate source IPs and bypass rate limits
- **MediaFlow Proxy**: Proxy DRM-protected streams and bypass IP restrictions

## Troubleshooting

### 403 errors with Torrentio

Torrentio blocks Oracle VPS IPs. Use the proxy services:
1. Enable WARP + MediaFlow Proxy: `docker compose --profile proxy up`
2. Configure AIOStreams to use MediaFlow Proxy as the transport route
3. This routes Torrentio requests through WARP to bypass IP blocks

### "Copy Install URL" does nothing

This is a known bug in self-hosted instances:
- Make sure you're running HTTPS (port 443)
- Try manually copying the URL from browser devtools

### Jackett not working

Ensure indexers are configured and the Jackett API key is added to AIOStreams.

### Hosting on free tiers (HuggingFace/Render)

**Don't do it.** You will get kicked. Free tiers aren't meant for media streaming bandwidth.
- Use Oracle Cloud Free Tier (10TB egress, 1Gbps)
- Use Hetzner or a cheap VPS
- Run at home with proper port forwarding