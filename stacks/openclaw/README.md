# OpenClaw Stack

Personal AI assistant stack. Deployed via Komodo, exposed at `https://<OPENCLAW_FQDN>`.

Compose file: `stacks/openclaw/compose.yaml`

## In Komodo

1. Create or open the `openclaw` stack.
2. Set run directory to `stacks/openclaw`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy).
5. Run onboarding via SSH (see below).
6. Approve yourself via the CLI.

## Stack environment variables

| Variable | Required | Description |
|---|---|---|
| `OPENCLAW_GATEWAY_TOKEN` | Yes | Gateway auth token. Generate with: `openssl rand -hex 32` |
| `OPENCLAW_TELEGRAM_BOT_TOKEN` | Optional | Telegram bot token from @BotFather (set after onboarding) |
| `OPENCLAW_FQDN` | Yes | Public hostname. Example: `openclaw.fewa.app` |
| `OPENCLAW_CONFIG_DIR` | Yes | Host path for config. Default: `/opt/openclaw/config` |
| `OPENCLAW_WORKSPACE_DIR` | Yes | Host path for workspace. Default: `/opt/openclaw/workspace` |
| `SHARED_DOCKER_NETWORK` | Optional | Shared proxy network. Default: `internal-network` |

## First-time setup

### 1. Create directories on VPS

```bash
ssh -p 2222 deploy@<vps-ip>
sudo mkdir -p /opt/openclaw/config /opt/openclaw/workspace
sudo chown 1000:1000 /opt/openclaw/config /opt/openclaw/workspace
sudo chmod 700 /opt/openclaw/config /opt/openclaw/workspace
```

### 2. Deploy the stack in Komodo

Set the environment variables in Komodo (see above), then Deploy.

### 3. Run onboarding

```bash
# SSH to VPS
ssh -p 2222 deploy@<vps-ip>

# Run onboarding
docker compose --profile cli run --rm openclaw-cli onboard --mode local --no-install-daemon
```

Follow the prompts to set up your model provider.

### 4. Apply security hardening

After onboarding, apply the hardened config:

```bash
docker compose --profile cli run --rm openclaw-cli config set gateway.mode local
docker compose --profile cli run --rm openclaw-cli config set gateway.bind lan
docker compose --profile cli run --rm openclaw-cli config set gateway.trustedProxies '["127.0.0.1","172.0.0.0/8"]'
docker compose --profile cli run --rm openclaw-cli config set session.dmScope per-channel-peer
docker compose --profile cli run --rm openclaw-cli config set tools.profile messaging
docker compose --profile cli run --rm openclaw-cli config set 'tools.deny' '["group:automation","group:runtime","group:fs","sessions_spawn","sessions_send"]'
docker compose --profile cli run --rm openclaw-cli config set tools.fs.workspaceOnly true
docker compose --profile cli run --rm openclaw-cli config set 'tools.exec' '{"security":"deny","ask":"always"}'
docker compose --profile cli run --rm openclaw-cli config set tools.elevated.enabled false
docker compose --profile cli run --rm openclaw-cli config set channels.telegram.enabled true
docker compose --profile cli run --rm openclaw-cli config set channels.telegram.dmPolicy pairing
docker compose --profile cli run --rm openclaw-cli config set discovery.mdns.mode off
docker compose --profile cli run --rm openclaw-cli config set controlUi.allowedOrigins '["https://<your-fqdn>"]'
docker compose --profile cli run --rm openclaw-cli config set logging.redactSensitive true
```

Restart the gateway:
```bash
docker compose restart openclaw-gateway
```

### 5. Add Telegram channel

```bash
docker compose --profile cli run --rm openclaw-cli channels add --channel telegram --token "<bot-token>"
```

### 6. Approve yourself

DM your Telegram bot. You'll receive a pairing code. Then:

```bash
docker compose --profile cli run --rm openclaw-cli pairing list telegram
docker compose --profile cli run --rm openclaw-cli pairing approve telegram <code>
```

### 7. Update DNS

Add a CNAME record in Cloudflare:
- Type: CNAME, Name: openclaw, Content: fewa.app, Proxy: Proxied

## Common tasks

### Access Control UI

Open `https://<OPENCLAW_FQDN>` in your browser and paste the gateway token.

### Run CLI commands

```bash
docker compose --profile cli run --rm openclaw-cli <command>
```

Useful commands: `devices list`, `pairing list telegram`, `security audit`, `config show`.

### Check logs

```bash
docker logs -f infra-openclaw-1
```

### Run a security audit

```bash
docker compose --profile cli run --rm openclaw-cli security audit
docker compose --profile cli run --rm openclaw-cli security audit --deep
```

### Update OpenClaw

```bash
# SSH to VPS
ssh -p 2222 deploy@<vps-ip>

# Pull latest image
docker pull ghcr.io/openclaw/openclaw:main-arm64

# Restart
docker compose -f /opt/komodo/stacks/openclaw/compose.yaml up -d
```

## Security hardening

This stack applies the [OpenClaw hardened baseline](https://docs.openclaw.ai/gateway/security):

- Gateway bound to `lan` (Docker internal network, reachable from Traefik)
- All WebSocket clients authenticated via gateway token
- Traefik acts as HTTPS terminator
- Telegram DMs gated via pairing (unknown senders must be approved)
- `session.dmScope: per-channel-peer` (DM isolation per sender)
- Tools: `messaging` profile with automation/runtime/fs groups denied
- Exec: `security=deny, ask=always` (no exec without explicit approval)
- Elevated tools: disabled
- Filesystem: workspace-only (can't access host files outside workspace)
- mDNS: off (irrelevant on VPS, prevents LAN disclosure)
- Control UI: `allowedOrigins` restricted to HTTPS domain
- Log redaction: enabled
- Host directories: `700` owned by uid 1000 (container's node user)
- Container: read-only root filesystem with writable bind mounts
- DOCKER-USER iptables rules block unexpected Docker port access
