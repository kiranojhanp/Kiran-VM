# Uptime Kuma Stack

Compose file: `stacks/uptime-kuma/compose.yaml`

## In Komodo

1. Create or open the `uptime-kuma` stack.
2. Set compose path to `stacks/uptime-kuma/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<UPTIME_KUMA_HOST>`.

## Stack environment variables

- `UPTIME_KUMA_HOST` (required): public hostname. Example: `uptime.fewa.app`.
- `TZ` (optional): timezone. Default: `UTC`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## Notes

- Uses SQLite for data storage.
- Monitors HTTP/HTTPS endpoints, TCP ports, ping, DNS, and Docker containers.
- WebSocket support is enabled via Traefik for real-time dashboard updates.
- Resource usage is lightweight (~80MB RAM with 50 monitors at 60s intervals).
- First visit: create an admin account via the web UI.

## Security

This stack includes Docker security hardening:

- **Read-only root filesystem**: Prevents container from writing to root filesystem
- **No new privileges**: Prevents privilege escalation attacks
- **Dropped all capabilities**: Removes all Linux capabilities (`cap_drop: ALL`)
- **Memory limits**: `mem_limit` and `memswap_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit: 100` prevents fork bombs
