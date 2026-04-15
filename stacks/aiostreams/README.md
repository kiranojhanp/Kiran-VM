# AIOStreams Stack

Compose file: `stacks/aiostreams/compose.yaml`

## In Komodo

1. Create or open the `aiostreams` stack.
2. Set compose path to `stacks/aiostreams/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<AIOSTREAMS_HOST>`.

## Stack environment variables

### Required

- `AIOSTREAMS_HOST` (required): public hostname. Example: `aiostreams.fewa.app`.
- `AIOSTREAMS_SECRET_KEY` (required): 64-character hex secret key. Generate with: `openssl rand -hex 32`

### Optional

- `JACKETT_HOST` (optional): hostname for Jackett UI. Default: `jackett.fewa.app`.
- `AIOSTREAMS_BASE_URL` (optional): base URL with protocol. Default: `https://aiostreams.fewa.app`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `PUID` (optional): user ID for file ownership. Default: `1000`.
- `PGID` (optional): group ID for file ownership. Default: `1000`.
- `TZ` (optional): timezone. Default: `UTC`.
- `AIOSTREAMS_TAG` (optional): image tag. Default: `latest`.
- `JACKETT_TAG` (optional): image tag. Default: `latest`.

## Setup

### AIOStreams Configuration

Create a `.env` file in the stack directory with the following:

```
# TorBox API (get from TorBox dashboard)
TORBOX_API_KEY=your_torbox_api_key

# Enable built-in addons (recommended for TorBox Pro users)
AIOSTREAMS_BUILTIN_ADDONS=true
```

### Jackett Integration

1. Add indexers in Jackett UI at `https://<JACKETT_HOST>` or `http://<JACKETT_HOST>:9117`
2. Configure AIOStreams to use Jackett as the indexer source

### How Content Sources Work

| Source | Description |
|--------|-------------|
| **TorBox (built-in)** | Already cached content - fast, reliable |
| **Torrentio (via Jackett)** | Finds torrents, sends to debrid - fills gaps |

When TorBox doesn't have content, AIOStreams falls back to Torrentio via Jackett.

### Bypassing Torrentio Blocks

Torrentio blocks Oracle IPs. Use Cloudflare Warp to bypass:

1. Warp runs as a SOCKS5 proxy on port 1080
2. Configure Jackett to use the proxy:
   ```
   HTTP_PROXY=socks5h://warp:1080
   HTTPS_PROXY=socks5h://warp:1080
   ```
   Or configure in Jackett UI under Settings > General.

## Services

| Service | Port | Purpose |
|---------|------|---------|
| AIOStreams | 3000 | Stremio addon server |
| Jackett | 9117 | Torrent indexer proxy |
| Cloudflare Warp | 1080 | SOCKS5 proxy to bypass IP blocks |

## Security

This stack includes Docker security hardening:

- **Read-only root filesystem**: Prevents container from writing to root filesystem
- **No new privileges**: Prevents privilege escalation attacks
- **Dropped all capabilities**: Removes all Linux capabilities (`cap_drop: ALL`)
- **Memory limits**: `mem_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit: 100` prevents fork bombs