# LobeHub Stack

Compose file: `stacks/lobehub/compose.yaml`

[LobeHub](https://lobehub.com) (formerly LobeChat) is an open-source, extensible AI chat platform
with multi-provider support, agents, knowledge base (RAG), and file upload. This stack runs the
**server database edition** of LobeHub behind `https://chat.fewa.app`.

## In Komodo

1. Create or open the `lobehub` stack.
2. Set run directory to `stacks/lobehub`.
3. Set compose path to `stacks/lobehub/compose.yaml`.
4. Add the variables below in the stack Environment.
5. Deploy (or Redeploy), then open `https://chat.fewa.app`.

## Stack environment variables

Required:

- `LOBEHUB_HOST` (required): public hostname. Example: `chat.fewa.app`.
- `POSTGRES_PASSWORD` (required): password for the in-stack Postgres superuser (`postgres`). Generate with: `openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24`.
- `KEY_VAULTS_SECRET` (required): encrypts sensitive data (e.g. stored provider API keys). Generate with: `openssl rand -base64 32`. **Keep this stable** — changing it makes encrypted data undecryptable.
- `AUTH_SECRET` (required): Better Auth session encryption key. Generate with: `openssl rand -base64 32`.
- `REDIS_PASSWORD` (required): password for the shared infra Redis (`redis_password` from `provision/secrets.yml`).
- `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` (required): Garage access key pair for the `lobe` bucket (see [Garage storage](#garage-storage)).
- `AUTH_ALLOWED_EMAILS` (required): comma-separated emails/domains allowed to register, e.g. `fewa.app,me@example.com`. The stack fails closed without it, so public signups cannot happen by accident.

Optional:

- `LOBEHUB_VERSION` (optional): image tag. Default: `2.2.19`.
- `LOBE_DB_NAME` (optional): database name. Default: `lobe`.
- `S3_BUCKET` (optional): Garage bucket name. Default: `lobe`.
- `S3_REGION` (optional): Garage region. Default: `ap-southeast-1`.
- `S3_GARAGE_HOST` (optional): public Garage S3 hostname. Default: `s3.fewa.app`.
- `SHARED_REDIS_HOST` (optional): shared Redis host. Default: `infra-redis-1`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `SHARED_INFRA_NETWORK` (optional): shared infra network for Redis. Default: `infra_net`.

## Database

This stack runs its **own** Postgres (`paradedb/paradedb:latest-pg17`) rather than the centralized
`infra-postgres-1`, because LobeHub needs the `pgvector` (RAG/knowledge base) and `pg_search`
(full-text search) extensions, which the shared Postgres image does not ship.

Data lives in the `lobe_pg_data` volume. LobeHub runs its own migrations on startup; watch for
`✅ database migration pass` in `docker logs -f lobehub`.

> **Backups:** this database is **not** covered by the WAL-G pipeline (which targets
> `infra-postgres-1`). Back it up with a periodic dump, e.g.:
> ```bash
> docker exec lobehub-postgres pg_dump -U postgres lobe | gzip > lobe-$(date +%F).sql.gz
> ```

## Garage storage

LobeHub stores uploads and knowledge-base files in the existing Garage S3 service
(`stacks/garage`). Create a dedicated bucket and key after Garage is deployed:

```bash
# Create a key for LobeHub and note the Key ID (GK...) and Secret key it prints
docker exec garage garage key create lobe

# Create the bucket and grant the key full access
docker exec garage garage bucket create lobe
docker exec garage garage bucket allow lobe --read --write --owner --key <LOBE_KEY_ID>
```

Set `S3_ACCESS_KEY_ID` (the Garage Key ID, e.g. `GK...`) and `S3_SECRET_ACCESS_KEY` in the
Komodo stack Environment.

Then set a **bucket CORS rule** so browsers can upload via presigned URLs. Garage implements the
S3 `PutBucketCors` API, so use any S3 client. Run this from the VM (the `amazon/aws-cli` image is
the zero-install option; it joins the Docker network to reach Garage):

```bash
cat > /tmp/lobe-cors.json <<'JSON'
{ "CORSRules": [
  { "AllowedOrigins": ["https://chat.fewa.app"],
    "AllowedMethods": ["GET", "PUT", "HEAD", "POST"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600 }
] }
JSON

docker run --rm -v /tmp/lobe-cors.json:/cors.json \
  -e AWS_ACCESS_KEY_ID=<LOBE_KEY_ID> -e AWS_SECRET_ACCESS_KEY=<LOBE_SECRET> \
  -e AWS_DEFAULT_REGION=ap-southeast-1 \
  --network internal-network amazon/aws-cli \
  --endpoint-url http://garage:3900 \
  s3api put-bucket-cors --bucket lobe --cors-configuration file:///cors.json
```

- Internal S3 endpoint (server-side): `http://garage:3900`
- Public S3 endpoint (presigned browser uploads): `https://s3.fewa.app`
- Path-style access is enabled (`S3_ENABLE_PATH_STYLE=1`), matching Garage.

The `garage` container must be on the same Docker network as `lobe` (the shared
`internal-network`), which it is by default.

## Authentication

LobeHub uses its built-in [Better Auth](https://www.better-auth.com) with email/password. Restrict
who can register with `AUTH_ALLOWED_EMAILS`. Users log in at `https://chat.fewa.app` and can add
their own model provider API keys in the UI (encrypted at rest with `KEY_VAULTS_SECRET`).

To add Authentik SSO later, create an OAuth2/OpenID provider in Authentik with redirect URI
`https://chat.fewa.app/api/auth/callback/authentik` and set:

```yaml
AUTH_SSO_PROVIDERS: authentik
AUTH_AUTHENTIK_ID: <client id>
AUTH_AUTHENTIK_SECRET: <client secret>
AUTH_AUTHENTIK_ISSUER: https://authentik.fewa.app/application/o/lobehub/
```

## Notes

- Traefik routes to the `lobe` service on port `3210`. WebSockets are handled automatically.
- HTTPS is terminated at Traefik; `APP_URL` is set to `https://${LOBEHUB_HOST}`.
- Agent Gateway (Gateway Mode) is intentionally **not** enabled — agent runs execute in the
  browser. Add the `lobehub-gateway` service and `ENABLE_AGENT_GATEWAY=1` later if needed.

## Security

- **Memory limits**: `mem_limit` / `memswap_limit` prevent resource exhaustion.
- **Process limits**: `pids_limit` prevents fork bombs.
- The in-stack Postgres listens only on the stack-internal `lobe_internal` network (no host port).
