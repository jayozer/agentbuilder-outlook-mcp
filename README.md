# MCP Outlook Server

FastMCP server for sending Outlook mail via Microsoft Graph. This project exists because the Agent Builder Outlook connector does not provide a send-email capability; the MCP server delivers that missing tool by exposing a single `send_outlook_mail` entry point that validates payloads, obtains access tokens, and calls the Graph `sendMail` endpoint.

## Prerequisites
- Python 3.10+
- Microsoft Outlook/Graph account with `Mail.Send` permission (delegated token or app registration)
- `uv` (recommended) or `pip`

## Installation
```bash
uv pip install .
```

## Environment Variables
Set the following in `.env` (create from `.env.example`):

- `GRAPH_USER_ACCESS_TOKEN` – Optional delegated bearer token (e.g., from Graph Explorer) for quick testing.
- `GRAPH_DEFAULT_SENDER` – Mailbox to send from, e.g., `user@outlook.com`.
- `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET` – Required only for app-only client credentials flow.

Load them before running:

```bash
set -a; source .env; set +a
```

## Local Usage
Dry run (no email sent):
```bash
python3 - <<'PY'
from server import send_outlook_mail_impl

result = send_outlook_mail_impl(
    subject="Dry Run",
    body="Payload preview only.",
    to=["recipient@example.com"],
    dry_run=True,
)
print(result)
PY
```

Send a live message (`dry_run=False`) once configuration is confirmed. To expose the MCP tool to clients:

```bash
fastmcp run server.py
```

## Testing
```bash
uv pip install .[dev]
pytest
```

Unit tests cover token acquisition and payload construction.

## Deployment Notes
- `fastmcp.json` is configured for `fastmcp run` and FastMCP Cloud.
- Secrets should be supplied via environment variables on the target platform.
- See `todo.md` for remaining tasks and deployment checklist.
