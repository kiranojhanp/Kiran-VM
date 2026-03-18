# Portabase stack

This stack deploys:

- Portabase dashboard (`portabase`)
- Portabase internal Postgres (`db`)
- Portabase backup agent (`agent`)

## Required env vars

Copy `stacks/portabase/.env.example` into your stack/environment secrets and set:

- `PORTABASE_PROJECT_SECRET`
- `PORTABASE_POSTGRES_PASSWORD`
- `PORTABASE_AGENT_EDGE_KEY`

## Agent database config

The agent reads config from `/data/config.json`.
This stack binds `stacks/portabase/agent/databases.json` directly to that path.

- Keep `stacks/portabase/agent/databases.json` as a regular file.
- If the file is missing, deploy fails fast (`create_host_path: false`) instead of creating a bad directory mount.

By default it starts empty:

```json
{
  "databases": []
}
```

Add each database you want Portabase to back up in this file using Portabase's documented schema.
