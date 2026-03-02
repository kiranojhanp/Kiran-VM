"""
Sure stack deploy — mirrors ansible/roles/sure/tasks/main.yml.
Sure is a Rails app; it connects to the shared infra postgres and redis via
the external `infra_net` Docker network.
"""

from pyinfra.operations import files, server
from utils import tpl

# ── 1. Create sure directory ──────────────────────────────────────────────────
files.directory(
    name="Create directory /opt/sure",
    path="/opt/sure",
    present=True,
    user="deploy",
    group="deploy",
    mode="750",
    _sudo=True,
)

# ── 2. Template docker-compose.yml ───────────────────────────────────────────
tpl(
    name="Template sure docker-compose.yml",
    src="templates/sure/docker-compose.yml.j2",
    dest="/opt/sure/docker-compose.yml",
    _sudo=True,
)

# ── 3. Template .env (mode 600 — contains secrets) ───────────────────────────
tpl(
    name="Template sure .env",
    src="templates/sure/sure.env.j2",
    dest="/opt/sure/.env",
    mode="600",
    _sudo=True,
)

# ── 4. Pull images and start stack ───────────────────────────────────────────
server.shell(
    name="Start sure stack",
    commands=[
        "docker compose -f /opt/sure/docker-compose.yml pull",
        "docker compose -f /opt/sure/docker-compose.yml up -d --remove-orphans",
    ],
    _sudo=True,
)
