# OpenClaw VPS Stack — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy OpenClaw as a hardened personal assistant on the Oracle Cloud VPS via Docker + Komodo, behind Traefik, with Telegram as the messaging channel.

**Architecture:** Two-container Docker Compose stack (`openclaw-gateway` + `openclaw-cli`) on the `internal-network`, exposed via Traefik at `openclaw.<domain>` with HTTPS + LetsEncrypt. Config and workspace persisted to host bind mounts. Gateway bound to `lan` (Docker internal), trusted to Traefik's Docker network. All DMs gated via pairing. Exec, automation, and runtime tool groups disabled by default.

**Tech Stack:** OpenClaw official image (`ghcr.io/openclaw/openclaw:main-arm64`), Docker Compose, Traefik (existing), Ansible, Komodo (existing stack deployment).

---

## Prerequisite

Ensure you have a Telegram bot token before starting. Create one via [@BotFather](https://t.me/BotFather) if you don't have one.

---

## Task 1: Add DOCKER-USER iptables rules

**Files:**
- Modify: `provision/roles/common/templates/rules.v4.j2`

Docker's published ports bypass the regular `INPUT` chain. The `DOCKER-USER` chain lets us filter Docker traffic at the host level before it reaches containers. This ensures that even if a container misconfigures its port exposure, unexpected traffic is blocked.

OpenClaw's gateway binds to `lan` (reachable from the Docker network). Without DOCKER-USER rules, Docker's forwarding would accept traffic from anywhere. The rules below lock it to internal Docker networks and established connections.

**Step 1: Add DOCKER-USER chain before COMMIT in rules.v4.j2**

Find the `COMMIT` under `*filter` (around line 49) and insert the DOCKER-USER rules just before it:

```diff
  # ── Default: DROP everything else (set by chain policy above) ──────────────

+ # ── Docker published ports hardening ────────────────────────────────────────
+ # DOCKER-USER is evaluated before Docker's own NAT rules.
+ # Allow established/related connections through.
+ -A DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
+ # Allow loopback.
+ -A DOCKER-USER -s 127.0.0.0/8 -j RETURN
+ # Allow Docker bridge networks (172.16–172.31 range covers default Docker DHCP range).
+ -A DOCKER-USER -s 172.16.0.0/12 -j RETURN
+ # Allow infra network (existing infra_net bridge).
+ -A DOCKER-USER -s 172.19.0.0/16 -j RETURN
+ # Allow Traefik-published web traffic from anywhere (HTTPS already terminates here).
+ -A DOCKER-USER -p tcp --dport 80 -j RETURN
+ -A DOCKER-USER -p tcp --dport 443 -j RETURN
+ # Drop everything else attempting to reach Docker-published ports.
+ -A DOCKER-USER -m conntrack --ctstate NEW -j DROP
+ -A DOCKER-USER -j RETURN

  COMMIT
```

Note: The existing `COMMIT` at the bottom of the file (line 50) marks the end of the `*filter` table. The new rules go just before it. Do not confuse this with the `*nat` COMMIT on line 57.

**Step 2: Commit**

```bash
git add provision/roles/common/templates/rules.v4.j2
git commit -m "security(common): add DOCKER-USER iptables rules

Block unexpected traffic to Docker-published ports at the host level.
Allow loopback, Docker bridge networks, and HTTP/HTTPS. Drop everything else.
```

---

## Task 2: Add OpenClaw Ansible variables

**Files:**
- Modify: `provision/group_vars/all.yml`

**Step 1: Add OpenClaw variables to group_vars/all.yml**

Append before the last blank line (after `redis_container_name`):

```yaml
# ── OpenClaw ──────────────────────────────────────────────────────────────────
openclaw_fqdn: "openclaw.{{ domain }}"
openclaw_config_dir: /opt/openclaw/config
openclaw_workspace_dir: /opt/openclaw/workspace
```

**Step 2: Commit**

```bash
git add provision/group_vars/all.yml
git commit -m "feat(common): add OpenClaw Ansible variables

openclaw_fqdn, openclaw_config_dir, openclaw_workspace_dir for stack deployment."
```

---

## Task 3: Add OpenClaw directory creation to Ansible

**Files:**
- Modify: `provision/roles/infra/tasks/main.yml` (or create `provision/roles/openclaw/tasks/main.yml`)

Using the infra role keeps it simple — it already handles directory creation for other services.

**Step 1: Add directory creation tasks to infra role**

Find the end of `provision/roles/infra/tasks/main.yml` (after the Postgres/Redis compose task) and append:

```yaml
# ── OpenClaw directories ──────────────────────────────────────────────────────
- name: Create OpenClaw config directory
  ansible.builtin.file:
    path: "{{ openclaw_config_dir }}"
    state: directory
    owner: "1000"
    group: "1000"
    mode: "0700"

- name: Create OpenClaw workspace directory
  ansible.builtin.file:
    path: "{{ openclaw_orkspace_dir }}"
    state: directory
    owner: "1000"
    group: "1000"
    mode: "0700"
```

Note: `1000` is the uid of the `node` user inside the OpenClaw container image. OpenClaw runs as non-root inside the container; the image uses uid 1000.

**Step 2: Commit**

```bash
git add provision/roles/infra/tasks/main.yml
git commit -m "feat(infra): create OpenClaw config and workspace host directories"
```

**Step 3: Verify the infra role runs cleanly**

```bash
cd /Users/kiranojha/development/kiran-vm
task update
```

Expected: Ansible completes without errors for the infra role tasks. The directories will be created on the VPS.

---

## Task 4: Create OpenClaw compose stack

**Files:**
- Create: `stacks/openclaw/compose.yaml`
- Create: `stacks/openclaw/.env.example`

**Step 1: Create stacks/openclaw directory**

```bash
mkdir -p stacks/openclaw
```

**Step 2: Write stacks/openclaw/compose.yaml**

```yaml
services:
  openclaw-gateway:
    image: ghcr.io/openclaw/openclaw:main-arm64
    restart: unless-stopped
    environment:
      OPENCLAW_GATEWAY_TOKEN: ${OPENCLAW_GATEWAY_TOKEN:?OPENCLAW_GATEWAY_TOKEN is required}
    volumes:
      - ${OPENCLAW_CONFIG_DIR}:/home/node/.openclaw:rw
      - ${OPENCLAW_WORKSPACE_DIR}:/home/node/.openclaw/workspace:rw
    networks:
      - shared
    labels:
      traefik.enable: "true"
      traefik.docker.network: ${SHARED_DOCKER_NETWORK:-internal-network}
      traefik.http.routers.openclaw.rule: Host(`${OPENCLAW_FQDN:?OPENCLAW_FQDN is required}`)
      traefik.http.routers.openclaw.entrypoints: websecure
      traefik.http.routers.openclaw.tls: "true"
      traefik.http.routers.openclaw.tls.certresolver: letsencrypt
      traefik.http.services.openclaw.loadbalancer.server.port: "18789"
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:18789/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    mem_limit: 1g
    memswap_limit: 1g
    read_only: true
    security_opt:
      - no-new-privileges:true

  openclaw-cli:
    image: ghcr.io/openclaw/openclaw:main-arm64
    profiles:
      - cli
    environment:
      OPENCLAW_GATEWAY_TOKEN: ${OPENCLAW_GATEWAY_TOKEN:?OPENCLAW_GATEWAY_TOKEN is required}
    volumes:
      - ${OPENCLAW_CONFIG_DIR}:/home/node/.openclaw:rw
      - ${OPENCLAW_WORKSPACE_DIR}:/home/node/.openclaw/workspace:rw
    network_mode: "service:openclaw-gateway"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    security_opt:
      - no-new-privileges:true

networks:
  shared:
    name: ${SHARED_DOCKER_NETWORK:-internal-network}
    external: true
```

Key design decisions:
- `read_only: true` on gateway — filesystem is immutable except for the bind mounts.
- `network_mode: "service:openclaw-gateway"` on CLI — shares the gateway's network stack, so `openclaw-cli` commands reach `127.0.0.1:18789` without publishing ports.
- `profiles: ["cli"]` — the CLI container only starts when you explicitly want it (`docker compose --profile cli up`).
- Healthcheck uses `/healthz` (no auth required) so Traefik or Docker can monitor it.
- Memory limits prevent runaway resource usage.
- `mem_limit` and `memswap_limit` equal means no swap within the container (OOM kills rather than swap thrashing).

**Step 3: Write stacks/openclaw/.env.example**

```bash
# Required — generate with: openssl rand -hex 32
OPENCLAW_GATEWAY_TOKEN=

# Required — your Telegram bot token from @BotFather
OPENCLAW_TELEGRAM_BOT_TOKEN=

# Domain — must resolve to your VPS
OPENCLAW_FQDN=openclaw.fewa.app

# Host paths for persistence — must exist on host with uid 1000:1000
OPENCLAW_CONFIG_DIR=/opt/openclaw/config
OPENCLAW_WORKSPACE_DIR=/opt/openclaw/workspace

# Shared Docker network — don't change unless you changed internal-network
SHARED_DOCKER_NETWORK=internal-network
```

**Step 4: Commit**

```bash
git add stacks/openclaw/
git commit -m "feat(openclaw): add compose stack with gateway + CLI containers

Gateway exposed via Traefik on openclaw.<domain> with HTTPS.
Config and workspace persisted to host bind mounts.
CLI container uses profile for on-demand exec commands."
```

---

## Task 5: Generate gateway token and wire into Komodo

**Files:**
- Modify: Komodo stack environment (set via Komodo web UI)

**Step 1: Generate a gateway token**

```bash
openssl rand -hex 32
```

Copy the output.

**Step 2: Set in Komodo**

1. Open Komodo web UI → find the OpenClaw stack.
2. In the **Environment** section, set these variables:

| Key | Value |
|-----|-------|
| `OPENCLAW_GATEWAY_TOKEN` | (output from step 1) |
| `OPENCLAW_TELEGRAM_BOT_TOKEN` | (your Telegram bot token) |
| `OPENCLAW_FQDN` | `openclaw.fewa.app` (or your domain) |
| `OPENCLAW_CONFIG_DIR` | `/opt/openclaw/config` |
| `OPENCLAW_WORKSPACE_DIR` | `/opt/openclaw/workspace` |

3. **Deploy** (or **Redeploy**) the stack in Komodo.

**Step 3: Verify container starts**

```bash
# SSH to VPS
ssh -p 2222 deploy@<your-vps-ip>

# Check container is running
docker ps | grep openclaw

# Tail logs
docker logs -f infra-openclaw-1 2>&1 | head -30
```

Expected: Container starts and logs show `listening on ws://0.0.0.0:18789`.

**Step 4: Verify Traefik routing**

```bash
curl -s -o /dev/null -w "%{http_code}" https://openclaw.fewa.app/healthz
```

Expected: `200` (or `401` if auth is enforced on healthz — both are fine).

---

## Task 6: Onboard OpenClaw via CLI

**Files:**
- None (exec commands into running container)

**Step 1: Run first-time onboarding via CLI exec**

```bash
docker compose --profile cli run --rm openclaw-cli onboard --mode local --no-install-daemon
```

This runs the interactive onboarding wizard non-interactively by passing `--mode local` (pre-configured mode) and `--no-install-daemon` (no systemd install inside container).

**Alternative — if the above fails, run interactively:**

```bash
docker compose run --rm -it openclaw-cli onboard --mode local --no-install-daemon
```

Then:
1. Paste your model provider API key when prompted (e.g., GitHub Copilot, OpenAI).
2. Follow the remaining prompts.

**Step 2: Verify config was written to host mount**

```bash
ls -la /opt/openclaw/config/
```

Expected: `openclaw.json` exists and is owned by uid 1000.

**Step 3: Set hardened openclaw.json config**

After onboarding, the config will have defaults. Apply the hardened settings via CLI:

```bash
# Set gateway mode
docker compose --profile cli run --rm openclaw-cli config set gateway.mode local
docker compose --profile cli run --rm openclaw-cli config set gateway.bind lan
docker compose --profile cli run --rm openclaw-cli config set gateway.trustedProxies '["127.0.0.1", "172.0.0.0/8"]'
docker compose --profile cli run --rm openclaw-cli config set gateway.tailscale.mode off

# Set session isolation
docker compose --profile cli run --rm openclaw-cli config set session.dmScope per-channel-peer

# Set tool hardening
docker compose --profile cli run --rm openclaw-cli config set tools.profile messaging
docker compose --profile cli run --rm openclaw-cli config set 'tools.deny' '["group:automation","group:runtime","group:fs","sessions_spawn","sessions_send"]'
docker compose --profile cli run --rm openclaw-cli config set tools.fs.workspaceOnly true
docker compose --profile cli run --rm openclaw-cli config set 'tools.exec' '{"security":"deny","ask":"always"}'
docker compose --profile cli run --rm openclaw-cli config set tools.elevated.enabled false

# Set Telegram channel
docker compose --profile cli run --rm openclaw-cli config set channels.telegram.enabled true
docker compose --profile cli run --rm openclaw-cli config set channels.telegram.dmPolicy pairing

# Disable mDNS (irrelevant on VPS)
docker compose --profile cli run --rm openclaw-cli config set discovery.mdns.mode off

# Set Control UI allowed origins
docker compose --profile cli run --rm openclaw-cli config set controlUi.allowedOrigins '["https://openclaw.fewa.app"]'

# Enable log redaction
docker compose --profile cli run --rm openclaw-cli config set logging.redactSensitive true
```

Alternatively, edit the file directly on the host:

```bash
vim /opt/openclaw/config/openclaw.json
```

And merge in the hardened config. Make sure the `gateway.auth.token` and `gateway.auth.mode` are preserved.

**Step 4: Restart gateway to pick up config changes**

```bash
docker compose restart openclaw-gateway
```

---

## Task 7: Add Telegram bot

**Files:**
- None (exec commands into running container)

**Step 1: Add Telegram channel**

```bash
docker compose --profile cli run --rm openclaw-cli channels add --channel telegram --token "${OPENCLAW_TELEGRAM_BOT_TOKEN}"
```

Replace `${OPENCLAW_TELEGRAM_BOT_TOKEN}` with the actual token (or run the command on the VPS with the env var set).

**Step 2: Verify Telegram bot is registered**

```bash
docker compose --profile cli run --rm openclaw-cli channels list
```

Expected output should list `telegram` as enabled.

---

## Task 8: Create stacks/openclaw/README.md

**Files:**
- Create: `stacks/openclaw/README.md`

```markdown
# OpenClaw

Personal AI assistant stack. Deployed via Komodo, exposed at `https://openclaw.<domain>`.

## Setup

### First-time deployment

1. **Create Telegram bot** at [@BotFather](https://t.me/BotFather) if you don't have one. Note the bot token.

2. **Generate gateway token**:
   ```bash
   openssl rand -hex 32
   ```

3. **Set Komodo environment variables** in the OpenClaw stack:

   | Variable | Value |
   |----------|-------|
   | `OPENCLAW_GATEWAY_TOKEN` | (from step 2) |
   | `OPENCLAW_TELEGRAM_BOT_TOKEN` | (from step 1) |
   | `OPENCLAW_FQDN` | `openclaw.fewa.app` |
   | `OPENCLAW_CONFIG_DIR` | `/opt/openclaw/config` |
   | `OPENCLAW_WORKSPACE_DIR` | `/opt/openclaw/workspace` |

4. **Deploy** the stack in Komodo.

5. **Run onboarding**:
   ```bash
   # SSH to VPS, then:
   docker compose --profile cli run --rm openclaw-cli onboard --mode local --no-install-daemon
   ```

6. **Add Telegram channel**:
   ```bash
   docker compose --profile cli run --rm openclaw-cli channels add --channel telegram --token "<your-bot-token>"
   ```

7. **Set hardened config** (after onboarding creates initial config):
   ```bash
   # Run each command:
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
   docker compose --profile cli run --rm openclaw-cli config set controlUi.allowedOrigins '["https://openclaw.fewa.app"]'
   docker compose --profile cli run --rm openclaw-cli config set logging.redactSensitive true
   ```

8. **Restart**:
   ```bash
   docker compose restart openclaw-gateway
   ```

9. **Approve yourself** — DM the Telegram bot. You'll receive a pairing code. Then:
   ```bash
   docker compose --profile cli run --rm openclaw-cli pairing list telegram
   docker compose --profile cli run --rm openclaw-cli pairing approve telegram <code>
   ```

## Common tasks

### Access Control UI

Open `https://openclaw.fewa.app` in your browser. Paste the gateway token from your Komodo env vars.

### Run CLI commands

```bash
docker compose --profile cli run --rm openclaw-cli <command>
```

Example commands: `devices list`, `pairing list telegram`, `security audit`, `config show`.

### Update OpenClaw

```bash
git pull
# Rebuild the image (if building locally) or pull the latest:
docker pull ghcr.io/openclaw/openclaw:main-arm64
docker compose up -d openclaw-gateway
```

### Check logs

```bash
docker logs -f infra-openclaw-1
```

### Run a security audit

```bash
docker compose --profile cli run --rm openclaw-cli security audit
docker compose --profile cli run --rm openclaw-cli security audit --deep
```

### Add more binaries (skills)

If you need additional binaries (e.g., `gog`, `goplaces`, `wacli`), you must bake them into a custom Docker image. See [Docker VM Runtime docs](https://docs.openclaw.ai/install/docker-vm-runtime).

## Security hardening

This stack uses the hardened baseline from [OpenClaw security docs](https://docs.openclaw.ai/gateway/security):

- Gateway bound to `lan` (Docker internal network, not host-exposed)
- All WebSocket clients authenticated via token
- Traefik acts as HTTPS terminator + auth gateway
- Telegram DMs gated via pairing (unknown senders must be approved)
- `session.dmScope: per-channel-peer` (DM isolation per sender)
- Tools: `messaging` profile with automation/runtime/fs groups denied
- Exec: `security=deny, ask=always` (no exec without explicit approval)
- Elevated tools: disabled
- Filesystem: workspace-only (can't access host files outside workspace)
- mDNS: off (irrelevant on VPS, prevents LAN disclosure)
- Tailscale: off
- Log redaction: enabled
- Control UI: `allowedOrigins` restricted to HTTPS domain
- Host directories: `700` owned by uid 1000 (container's node user)
- DOCKER-USER iptables rules on VPS block unexpected Docker port access
```

**Step 2: Commit**

```bash
git add stacks/openclaw/README.md
git commit -m "docs(openclaw): add README with setup, common tasks, and security notes"
```

---

## Task 9: Verify the full stack

**Files:**
- None (verification only)

**Step 1: Check all containers are healthy**

```bash
docker ps | grep openclaw
```

Expected: Both `openclaw-gateway` and `openclaw-cli` (if running) show status `Up`.

**Step 2: Check health endpoint**

```bash
curl -fsS https://openclaw.fewa.app/healthz
```

Expected: `200 OK` or similar health response.

**Step 3: Check Traefik routing**

```bash
curl -fsS -o /dev/null -w "%{http_code}" https://openclaw.fewa.app/
```

Expected: `200` or `401` (Control UI requires auth).

**Step 4: Run security audit**

```bash
docker compose --profile cli run --rm openclaw-cli security audit
```

Expected: No critical findings. The main things to watch for:
- `gateway.loopback_no_auth` — should be `warn` or lower (it's `lan` bind but with auth token set)
- `gateway.control_ui.allowed_origins_required` — should not appear if `allowedOrigins` is set
- `tools.exec.host_sandbox_no_sandbox_defaults` — expected if sandbox is off (it's off by default)
- `logging.redact_off` — should not appear

**Step 5: Test Telegram DM pairing flow**

1. Open Telegram, find your bot.
2. Send any message — you should receive a pairing code back.
3. Approve yourself:
   ```bash
   docker compose --profile cli run --rm openclaw-cli pairing list telegram
   docker compose --profile cli run --rm openclaw-cli pairing approve telegram <code>
   ```
4. Send another message — the bot should respond.

**Step 6: Test Web UI access**

1. Open `https://openclaw.fewa.app` in your browser.
2. Paste the gateway token when prompted.
3. The Control UI should load.

---

## Task 10: Update Cloudflare DNS

**Files:**
- Modify: Pulumi infra (if DNS is managed there) or Cloudflare dashboard

**Step 1: Add DNS record**

Add a CNAME record for `openclaw` pointing to your main domain:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | openclaw | fewa.app | Proxied |

If DNS is managed by Pulumi (`infra/__main__.py`), add it there. Otherwise, set it manually in Cloudflare.

---

## Verification Checklist

After all tasks complete, run through this checklist:

```
[ ] VPS: DOCKER-USER iptables rules applied and verified
[ ] VPS: /opt/openclaw/config and /opt/openclaw/workspace created with uid 1000:1000, mode 700
[ ] Container: openclaw-gateway running and healthy (docker ps)
[ ] Container: Traefik route active for openclaw.fewa.app (curl https healthz)
[ ] Config: gateway.bind = lan
[ ] Config: gateway.auth.token set
[ ] Config: gateway.trustedProxies includes Docker network range
[ ] Config: session.dmScope = per-channel-peer
[ ] Config: tools.profile = messaging
[ ] Config: tools.deny includes automation/runtime/fs groups
[ ] Config: tools.exec.security = deny
[ ] Config: channels.telegram.enabled = true
[ ] Config: channels.telegram.dmPolicy = pairing
[ ] Config: discovery.mdns.mode = off
[ ] Config: controlUi.allowedOrigins set to HTTPS domain
[ ] Config: logging.redactSensitive = true
[ ] Telegram: bot token set via CLI
[ ] Telegram: pairing approved for your Telegram user
[ ] Telegram: bot responds to DMs
[ ] Web UI: https://openclaw.fewa.app loads with token auth
[ ] Audit: openclaw security audit --deep shows no critical findings
```

---

## Rollback

If something breaks:

```bash
# Stop the stack
docker compose -f /opt/komodo/stacks/openclaw/compose.yaml down

# Remove the containers (config and workspace survive on host)
docker rmi ghcr.io/openclaw/openclaw:main-arm64

# Restart old version or debug
docker compose -f /opt/komodo/stacks/openclaw/compose.yaml up -d

# If config is corrupted, restore from backup
cp /opt/openclaw/config/openclaw.json.bak /opt/openclaw/config/openclaw.json
docker compose restart openclaw-gateway
```
