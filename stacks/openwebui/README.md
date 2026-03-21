# Open WebUI Stack

Compose file: `stacks/openwebui/compose.yaml`

## In Komodo

1. Create or open the `openwebui` stack.
2. Set compose path to `stacks/openwebui/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<OPENWEBUI_HOST>`.

## Stack environment variables

- `OPENWEBUI_HOST` (required): public hostname. Example: `openwebui.fewa.app`.
- `DATABASE_URL` (required): Postgres connection string for Open WebUI. Example: `postgresql://openwebui_user:<password>@infra-postgres-1:5432/openwebui`.
- `WEBUI_SECRET_KEY` (required): long random secret used for signing and encryption. Keep this stable across redeploys.
- `WEBUI_URL` (recommended): public URL used by Open WebUI. Example: `https://openwebui.fewa.app`.
- `CORS_ALLOW_ORIGIN` (recommended): allowed origins for browser access; use a semicolon-separated list for multiple origins.
- `OPENAI_API_KEYS` (optional): comma-separated API keys for OpenAI-compatible providers.
- `OPENAI_API_BASE_URLS` (optional): comma-separated base URLs. Default: `https://api.openai.com/v1`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `INFRA_DOCKER_NETWORK` (optional): network that contains the shared Postgres container. Default: `infra_net`.
