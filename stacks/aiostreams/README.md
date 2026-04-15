# AIOStreams Stack

Self-hosted Stremio addon aggregator with Jackett for custom torrent indexers.

## Quick Start

1. Create/open the `aiostreams` stack in Komodo
2. Set compose path to `stacks/aiostreams/compose.yaml`
3. Copy `.env.sample` to `.env` and fill in values
4. Add stack environment variables:
   - `AIOSTREAMS_HOST` = `aiostreams.fewa.app`
   - `JACKETT_HOST` = `jackett.fewa.app` (optional)
   - `SHARED_DOCKER_NETWORK` = `internal-network` (optional)
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

| Service | URL | Purpose |
|---------|-----|---------|
| AIOStreams | `https://aiostreams.fewa.app` | Stremio addon |
| Jackett | `https://jackett.fewa.app` | Torrent indexers |

## Troubleshooting

### 403 errors with Torrentio

Torrentio blocks Oracle VPS IPs. Options:
1. Disable Torrentio - use Jackett + other sources instead
2. Use a VPN proxy (gluetun) - see [AIOStreams docs](https://docs.aiostreams.viren070.me/getting-started/deployment/)

### Jackett not working

Ensure indexers are configured and the Jackett API key is added to AIOStreams.