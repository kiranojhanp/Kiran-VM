"""
Caddy reverse proxy deploy — mirrors ansible/roles/caddy/tasks/main.yml.
Uses a custom xcaddy build (Cloudflare DNS module) via Dockerfile.
"""

from pyinfra.operations import files, server
from utils import tpl

# ── 1. Create Caddy directories ───────────────────────────────────────────────
for path in ["/opt/caddy", "/opt/caddy/data", "/opt/caddy/config"]:
    files.directory(
        name=f"Create directory {path}",
        path=path,
        present=True,
        user="deploy",
        group="deploy",
        mode="750",
        _sudo=True,
    )

# ── 2. Template Caddyfile ─────────────────────────────────────────────────────
tpl(
    name="Template Caddyfile",
    src="templates/caddy/Caddyfile.j2",
    dest="/opt/caddy/Caddyfile",
    _sudo=True,
)

# ── 3. Template .env (mode 600 — contains Cloudflare API token) ───────────────
tpl(
    name="Template caddy .env",
    src="templates/caddy/caddy.env.j2",
    dest="/opt/caddy/.env",
    mode="600",
    _sudo=True,
)

# ── 4. Template docker-compose.yml ───────────────────────────────────────────
tpl(
    name="Template caddy docker-compose.yml",
    src="templates/caddy/docker-compose.yml.j2",
    dest="/opt/caddy/docker-compose.yml",
    _sudo=True,
)

# ── 5. Template Dockerfile (xcaddy custom build — Cloudflare DNS module) ──────
tpl(
    name="Template caddy Dockerfile",
    src="templates/caddy/Dockerfile.j2",
    dest="/opt/caddy/Dockerfile",
    _sudo=True,
)

# ── 6. Build image and start stack ───────────────────────────────────────────
server.shell(
    name="Start Caddy stack",
    commands=[
        "docker compose -f /opt/caddy/docker-compose.yml build",
        "docker compose -f /opt/caddy/docker-compose.yml up -d",
    ],
    _sudo=True,
)
