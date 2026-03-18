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

The agent reads `stacks/portabase/agent/databases.json`.

By default it starts empty:

```json
{
  "databases": []
}
```

Add each database you want Portabase to back up in this file using Portabase's documented schema.
