# Portabase stack

This stack runs three services:

- Portabase dashboard (`portabase`)
- Portabase Postgres (`db`)
- Portabase agent (`agent`)

## Before first deploy

Copy values from `stacks/portabase/.env.example` into your stack environment and set at least:

- `PORTABASE_PROJECT_SECRET`
- `PORTABASE_POSTGRES_PASSWORD`

Leave `PORTABASE_AGENT_EDGE_KEY` empty for the very first deploy. You will get it from the Portabase UI.

## Fresh deploy steps

1. Deploy `stacks/portabase/compose.yaml` from Komodo.
2. Open Portabase at your configured host (`PORTABASE_HOST`) and create your admin account.
3. In Portabase, create an agent and copy the Edge Key.
4. Set `PORTABASE_AGENT_EDGE_KEY` in stack env.
5. Redeploy the stack.
6. Confirm the agent shows online in the Portabase UI.

## Agent config file

The agent loads databases from `/data/config.json`.
That file is bind-mounted from `stacks/portabase/agent/databases.json`.

- Keep `stacks/portabase/agent/databases.json` as a file (not a directory).
- If the file is missing, deploy fails fast because `create_host_path: false` is enabled.

Default content:

```json
{
  "databases": []
}
```

Add your DB connections in this file using Portabase's documented schema.

## Quick verification after deploy

- Check agent logs and confirm there are no config/EDGE_KEY errors.
- Add one test database and run one manual backup.
- Run one restore test before trusting schedules.

## Troubleshooting

`EDGE_KEY missing` or `invalid EDGE_KEY`
- Generate a fresh Edge Key from the Portabase UI.
- Update `PORTABASE_AGENT_EDGE_KEY` and redeploy.

`Failed to read config file: Is a directory (os error 21)`
- The host path for `stacks/portabase/agent/databases.json` is a directory instead of a file.
- Check current mounts:

```bash
docker inspect portabase-agent-1 --format '{{range .Mounts}}{{println .Type "|" .Source "->" .Destination}}{{end}}'
```

- Repair the mounted source file and restart agent:

```bash
SRC=$(docker inspect portabase-agent-1 --format '{{range .Mounts}}{{if eq .Destination "/data/config.json"}}{{.Source}}{{end}}{{end}}')
sudo rm -rf "$SRC"
printf '{"databases":[]}\n' | sudo tee "$SRC" >/dev/null
sudo chmod 644 "$SRC"
docker restart portabase-agent-1
```

`compose.yaml: no such file or directory`
- You are likely using a stale server path.
- Redeploy from Komodo UI instead of using guessed local paths.

`Permission denied` while writing under `/opt/komodo/...`
- Use `sudo tee` for writes.
- `sudo printf ... > file` fails because shell redirection runs before sudo.
