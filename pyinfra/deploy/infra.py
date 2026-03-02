"""
Shared infrastructure — Postgres + Redis.
Mirrors ansible/roles/infra/tasks/main.yml.
Must run before any app deploy (sure, gitea, nocodb, etc.).
"""

from pyinfra.operations import files, server
from utils import tpl

# ── 1. Create /opt/infra directory ──────────────────────────────────────────
files.directory(
    name="Create /opt/infra directory",
    path="/opt/infra",
    present=True,
    user="deploy",
    group="deploy",
    mode="755",
    _sudo=True,
)

# ── 2. Deploy docker-compose.yml ─────────────────────────────────────────────
# Template var: infra_dir (all.py → "/opt/infra")
tpl(
    name="Template /opt/infra/docker-compose.yml",
    src="templates/infra/docker-compose.yml.j2",
    dest="/opt/infra/docker-compose.yml",
    user="deploy",
    group="deploy",
    mode="640",
    _sudo=True,
)

# ── 3. Deploy .env (secrets) ─────────────────────────────────────────────────
# Template var: shared_postgres_password (secrets.py)
tpl(
    name="Template /opt/infra/.env",
    src="templates/infra/infra.env.j2",
    dest="/opt/infra/.env",
    user="deploy",
    group="deploy",
    mode="600",
    _sudo=True,
)

# ── 4. Deploy Postgres init SQL ───────────────────────────────────────────────
# Template vars: shared_postgres_sure_password, shared_postgres_gitea_password,
#                shared_postgres_nocodb_password (all in secrets.py)
tpl(
    name="Template /opt/infra/init.sql",
    src="templates/infra/init.sql.j2",
    dest="/opt/infra/init.sql",
    user="deploy",
    group="deploy",
    mode="644",
    _sudo=True,
)

# ── 5. Pull infra images ──────────────────────────────────────────────────────
server.shell(
    name="Pull infra Docker images",
    commands=["docker compose -f /opt/infra/docker-compose.yml pull"],
    _sudo=True,
)

# ── 6. Start infra stack ──────────────────────────────────────────────────────
server.shell(
    name="Start infra stack (docker compose up -d)",
    commands=["docker compose -f /opt/infra/docker-compose.yml up -d"],
    _sudo=True,
)

# ── 7. Wait for Postgres to be healthy ───────────────────────────────────────
# 20 retries × 5s = up to 100s
server.shell(
    name="Wait for shared Postgres to be healthy",
    commands=[
        "for i in $(seq 1 20); do"
        " docker exec infra-postgres-1 pg_isready -U postgres && break"
        " || sleep 5;"
        " done"
    ],
    _sudo=True,
)

# ── 8. Wait for Redis to be healthy ──────────────────────────────────────────
# 10 retries × 3s = up to 30s
server.shell(
    name="Wait for shared Redis to be healthy",
    commands=[
        "for i in $(seq 1 10); do"
        " docker exec infra-redis-1 redis-cli ping | grep -q PONG && break"
        " || sleep 3;"
        " done"
    ],
    _sudo=True,
)
