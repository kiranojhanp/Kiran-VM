"""
NocoDB stack deploy — mirrors ansible/roles/nocodb/tasks/main.yml.
NocoDB is a no-code database UI backed by shared Postgres.
"""

from pyinfra.operations import files, server
from utils import tpl

# ── 1. Create nocodb directories ─────────────────────────────────────────────
for path in ["/opt/nocodb", "/opt/nocodb/data"]:
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
    name="Template nocodb docker-compose.yml",
    src="templates/nocodb/docker-compose.yml.j2",
    dest="/opt/nocodb/docker-compose.yml",
    _sudo=True,
)

# ── 3. Template .env (mode 600 — contains secrets) ───────────────────────────
tpl(
    name="Template nocodb .env",
    src="templates/nocodb/nocodb.env.j2",
    dest="/opt/nocodb/.env",
    mode="600",
    _sudo=True,
)

# ── 4. Pull images and start stack ───────────────────────────────────────────
server.shell(
    name="Start nocodb stack",
    commands=[
        "docker compose -f /opt/nocodb/docker-compose.yml pull",
        "docker compose -f /opt/nocodb/docker-compose.yml up -d",
    ],
    _sudo=True,
)
