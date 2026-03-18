# Open WebUI Stack

Compose file: `stacks/openwebui/compose.yaml`

## In Komodo

1. Create or open the `openwebui` stack.
2. Set compose path to `stacks/openwebui/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<OPENWEBUI_HOST>`.

## Stack environment variables

- `OPENWEBUI_HOST` (required): public hostname. Example: `openwebui.fewa.app`.
- `OPENAI_API_KEYS` (optional): comma-separated API keys for OpenAI-compatible providers.
- `OPENAI_API_BASE_URLS` (optional): comma-separated base URLs. Default: `https://api.openai.com/v1`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
