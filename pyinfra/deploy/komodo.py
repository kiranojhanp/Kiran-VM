"""
Komodo stack deploy — mirrors ansible/roles/komodo/tasks/main.yml.
Stack: postgres-documentdb → ferretdb → komodo-core + komodo-periphery.
"""

from pyinfra.operations import files, server
from utils import tpl

# ── 1. Create komodo directories ─────────────────────────────────────────────
for path in ["/opt/komodo", "/opt/komodo/data", "/opt/komodo/periphery"]:
    files.directory(
        name=f"Create directory {path}",
        path=path,
        present=True,
        user="deploy",
        group="deploy",
        mode="750",
        _sudo=True,
    )

# ── 2. Template docker-compose.yml ───────────────────────────────────────────
tpl(
    name="Template komodo docker-compose.yml",
    src="templates/komodo/docker-compose.yml.j2",
    dest="/opt/komodo/docker-compose.yml",
    _sudo=True,
)

# ── 3. Template .env (mode 600 — contains secrets) ───────────────────────────
tpl(
    name="Template komodo .env",
    src="templates/komodo/komodo.env.j2",
    dest="/opt/komodo/.env",
    mode="600",
    _sudo=True,
)

# ── 4. Pull images and start stack ───────────────────────────────────────────
server.shell(
    name="Start komodo stack",
    commands=[
        "docker compose -f /opt/komodo/docker-compose.yml pull",
        "docker compose -f /opt/komodo/docker-compose.yml up -d",
    ],
    _sudo=True,
)
