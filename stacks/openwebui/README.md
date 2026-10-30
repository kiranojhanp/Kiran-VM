# Open WebUI Stack

Compose file: `stacks/openwebui/compose.yaml`

Served at `https://chat.fewa.app` (this was its original hostname; see commit
`11de59a`).

## In Komodo

1. Create or open the **`openwebui`** stack.
2. Set run directory to `stacks/openwebui`.
3. Set compose path to `stacks/openwebui/compose.yaml`.
4. Add the variables below in the stack Environment.
5. Deploy (or Redeploy), then open `https://chat.fewa.app`.

> If the old `lobehub` stack still exists, **destroy it first** — both stacks
> would otherwise claim the `chat.fewa.app` Traefik route.

## Stack environment variables

- `OPENWEBUI_HOST` (optional): public hostname. Default: `chat.fewa.app`.
- `DATABASE_URL` (required): Postgres connection string. The `openwebui`
  database and `openwebui_user` role already exist on `infra-postgres-1`, and
  the role's password is `shared_postgres_password`:
  `postgresql://openwebui_user:<shared_postgres_password>@infra-postgres-1:5432/openwebui`
- `WEBUI_SECRET_KEY` (required): long random secret used for signing and
  encryption. **Reuse the existing value** — changing it invalidates sessions.
- `WEBUI_URL` (optional): public URL. Default: `https://chat.fewa.app`.
- `CORS_ALLOW_ORIGIN` (optional): allowed browser origin. Default:
  `https://chat.fewa.app`.
- `OPENAI_API_KEYS` (optional): comma-separated API keys for OpenAI-compatible providers.
- `OPENAI_API_BASE_URLS` (optional): comma-separated base URLs. Default: `https://api.openai.com/v1`.
- `OAUTH_CLIENT_ID` / `OAUTH_CLIENT_SECRET` (required): Authentik OIDC client
  credentials. Required because the login form is disabled; Compose fails
  closed if they are missing.
- `OPENID_PROVIDER_URL` (optional): Authentik discovery URL. Default:
  `https://authentik.fewa.app/application/o/open-web-ui/.well-known/openid-configuration`
  (the Authentik application slug is `open-web-ui`).
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `SHARED_INFRA_NETWORK` (optional): network with Postgres. Default: `infra_net`.
- `VANEWEBUI_HOST` (optional): Vane web UI hostname. Default: `vane.fewa.app`.

### Web Search (SearXNG + Vane)

Native web search is enabled via the built-in SearXNG integration. The
`searxng` service runs on the `infra` network and is reachable from Open WebUI
at `http://searxng:8080/search`. Web search is toggled on in the chat UI next
to the input box.

SearXNG configuration lives in `stacks/openwebui/searxng/settings.yml`. The
`json` format is required so Open WebUI can parse results. To regenerate the
config after a fresh pull of the SearXNG image:

```bash
docker compose up -d searxng
docker compose stop searxng
# edit stacks/openwebui/searxng/settings.yml as needed
docker compose up -d
```

### Vane (Perplexity-style AI Search)

Vane is a self-hosted, open-source AI-powered answering engine. It reads your
question, searches the live web through the shared SearXNG instance, and
composes a Perplexity-style answer with source citations. It uses the same
SearXNG backend as Open WebUI's native search.

- **Web UI**: `https://vane.fewa.app` (set `VANEWEBUI_HOST` to change)
- **Internal API**: `http://vane:3000` (on the `infra` network)
- **Data volume**: `openwebui_vane_data`

Vane is useful for testing its own search behavior independently of Open
WebUI. If you later decide you don't need the separate web UI, you can remove
the Vane service from this compose file without affecting Open WebUI's native
SearXNG integration.

### Authentik

The login form is disabled (`ENABLE_LOGIN_FORM=false`), so sign-in goes through
Authentik. The Authentik application is `open-web-ui`; its redirect URI is
already set to:

```
https://chat.fewa.app/oauth/oidc/callback
```

If you ever recreate the provider, add that URL as a strict redirect URI.

### Database

The database is **not** in `postgres_databases_list` (the role is named
`openwebui_user`, not `openwebui`), so it must already exist. Verify with:

```bash
docker exec infra-postgres-1 psql -U postgres -tAc \
  "SELECT datname, pg_get_userbyid(datdba) FROM pg_database WHERE datname='openwebui';"
```

To recreate it on a fresh host:

```bash
docker exec -e PGPASSWORD="$SHARED_POSTGRES_PASSWORD" infra-postgres-1 \
  psql -U postgres -c "CREATE USER openwebui_user WITH PASSWORD '$SHARED_POSTGRES_PASSWORD';"
docker exec -e PGPASSWORD="$SHARED_POSTGRES_PASSWORD" infra-postgres-1 \
  psql -U postgres -c "CREATE DATABASE openwebui OWNER openwebui_user;"
```

## Storage

Data lives in the named volume `openwebui_open_webui_data` (pinned explicitly,
~2.2G of existing data). It is **root-owned**, so the container runs as root;
do not add `user: 1000:1000` or it will fail to write.

## Security

- **No new privileges**: prevents privilege escalation
- **Memory limits**: `mem_limit` / `memswap_limit` bound resource use
- **Process limit**: `pids_limit: 200` (cgroup-based, per-container)
- No `nproc` ulimit: `RLIMIT_NPROC` is enforced per-UID host-wide and breaks
  `exec` when the UID is busy on the host.
