# Portabase stack

Compose file: `stacks/portabase/compose.yaml`

## In Komodo

1. Create or open the `portabase` stack.
2. Set compose path to `stacks/portabase/compose.yaml`.
3. Add the variables below in the stack Environment.
4. First deploy: keep `PORTABASE_AGENT_EDGE_KEY` empty.
5. Open `https://<PORTABASE_HOST>`, create admin, create agent, and copy Edge Key.
6. Set `PORTABASE_AGENT_EDGE_KEY` and Redeploy.

## Stack environment variables

- `PORTABASE_HOST` (required): public hostname. Example: `portabase.fewa.app`.
- `PORTABASE_PROJECT_SECRET` (required): random secret for the app.
- `PORTABASE_POSTGRES_PASSWORD` (required): database password.
- `PORTABASE_POSTGRES_DB` (optional): database name. Default: `portabase`.
- `PORTABASE_POSTGRES_USER` (optional): database user. Default: `portabase`.
- `PORTABASE_PROJECT_URL` (optional): full project URL. Default: `https://${PORTABASE_HOST}`.
- `PORTABASE_TZ` (optional): timezone for app containers. Default: `UTC`.
- `PORTABASE_AGENT_EDGE_KEY` (required after first deploy): agent Edge Key from Portabase UI.
- `PORTABASE_AGENT_TZ` (optional): agent timezone. Default: `UTC`.
- `PORTABASE_AGENT_POLLING` (optional): agent polling interval in seconds. Default: `5`.
- `PORTABASE_AGENT_LOG` (optional): agent log level. Default: `info`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.
- `SHARED_INFRA_NETWORK` (optional): infra network. Default: `infra_net`.

Keep `stacks/portabase/agent/databases.json` as a file. The agent mount expects that exact file path.
