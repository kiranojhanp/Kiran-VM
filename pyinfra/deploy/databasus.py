"""
Databasus stack deploy — mirrors ansible/roles/databasus/tasks/main.yml.
Databasus is a self-hosted backup tool with Cloudflare R2 storage.
"""

from pyinfra.operations import files, server
from utils import tpl

# ── 1. Create databasus directories ──────────────────────────────────────────
for path in ["/opt/databasus", "/opt/databasus/data"]:
    files.directory(
        name=f"Create directory {path}",
        path=path,
        present=True,
        user="deploy",
        group="deploy",
        mode="755",
        _sudo=True,
    )

# ── 2. Template docker-compose.yml ───────────────────────────────────────────
tpl(
    name="Template databasus docker-compose.yml",
    src="templates/databasus/docker-compose.yml.j2",
    dest="/opt/databasus/docker-compose.yml",
    _sudo=True,
)

# ── 3. Template .env (mode 600 — contains secrets) ───────────────────────────
tpl(
    name="Template databasus .env",
    src="templates/databasus/databasus.env.j2",
    dest="/opt/databasus/.env",
    mode="600",
    _sudo=True,
)

# ── 4. Pull images and start stack ───────────────────────────────────────────
server.shell(
    name="Start databasus stack",
    commands=[
        "docker compose -f /opt/databasus/docker-compose.yml pull",
        "docker compose -f /opt/databasus/docker-compose.yml up -d",
    ],
    _sudo=True,
)
