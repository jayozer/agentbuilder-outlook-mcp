# Agentbuilder Outlook MCP Server

[![FastMCP Deployment](https://img.shields.io/badge/FastMCP-Live-green)](https://agentbuilder-outlook-mcp.fastmcp.app/mcp)

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

## Remote Deployment

The server is deployed on FastMCP at `https://agentbuilder-outlook-mcp.fastmcp.app/mcp`. Connect your MCP-compatible client (Claude Desktop, Cursor, etc.) using this URL.

For local validation before hitting the remote server:

```bash
fastmcp run server.py
```

## Multi-Tenant Configuration

This server supports **multi-tenant usage** where each user provides their own Microsoft credentials when calling the `send_outlook_mail` tool.

### Two Authentication Methods

#### Method 1: Delegated Access Token (Testing/Personal Use)

Get a token from [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer):
1. Sign in to Graph Explorer
2. Grant `Mail.Send` permission
3. Copy the access token from the "Access Token" tab

Call the tool with your token:
```python
send_outlook_mail(
    subject="Test Email",
    body="Hello from multi-tenant MCP!",
    to=["recipient@example.com"],
    access_token="EwBIBMl6BAAU...",  # Your Graph Explorer token
    sender="your.email@example.com"
)
```

**Note:** Delegated tokens expire in ~1 hour.

#### Method 2: Client Credentials (Production/Service)

Create an Azure AD app registration with `Mail.Send` application permission, then:

```python
send_outlook_mail(
    subject="Automated Email",
    body="Sent via client credentials",
    to=["recipient@example.com"],
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    sender="mailbox@example.com"
)
```

### Single-Tenant Fallback

For backwards compatibility, if no credential parameters are provided, the server will fall back to environment variables:

- `GRAPH_TENANT_ID`
- `GRAPH_CLIENT_ID`
- `GRAPH_CLIENT_SECRET`
- `GRAPH_DEFAULT_SENDER`
- `GRAPH_USER_ACCESS_TOKEN`

This allows you to run a single-tenant server where all users share the same Outlook account.

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
