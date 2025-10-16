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

This server supports **multi-tenant usage** where each user provides their own Microsoft credentials when calling the `send_outlook_mail` tool. The server itself stores NO credentials - all authentication happens per-request.

### Two Authentication Methods

The MCP server supports both personal Microsoft accounts and organizational accounts through two different authentication flows:

#### Method 1: Personal Microsoft Accounts (@outlook.com, @hotmail.com, @live.com)

**Best for:** Individual users, testing, personal email automation

**Authentication:** Delegated permissions with user sign-in

**Setup Steps:**
1. Go to [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer)
2. Sign in with your personal Microsoft account
3. Run any query (e.g., GET /me)
4. Grant `Mail.Send` permission when prompted
5. Click the **"Access token"** tab and copy the token
6. Use the token in your MCP client:

```python
send_outlook_mail(
    subject="Test Email",
    body="Hello from my personal account!",
    to=["recipient@example.com"],
    access_token="EwBIBMl6BAAU...",  # Your Graph Explorer token
    sender="your.personal@outlook.com"
)
```

**Token Format:** Non-JWT proprietary format (starts with `EwB...`, no dots)
**Expiration:** ~1 hour (must refresh manually)
**Permissions:** Delegated (acts as the signed-in user)

**Note:** Personal account tokens use Microsoft's proprietary encrypted format. This is normal and works correctly with the Graph API, despite not being standard JWTs.

---

#### Method 2: Organizational Accounts (Microsoft 365 / Azure AD)

**Best for:** Production applications, service accounts, automated workflows

**Authentication:** Client credentials (application-only, no user sign-in)

**Prerequisites:**
- Azure AD tenant with Microsoft 365
- Exchange Online mailbox provisioned
- Azure AD app registration

**Setup Steps:** See [AZURE_SETUP.md](./AZURE_SETUP.md) for detailed instructions

**Quick Summary:**
1. Create Azure AD app registration
2. Add `Mail.Send` application permission
3. Grant admin consent
4. Create client secret
5. Use credentials in your MCP client:

```python
send_outlook_mail(
    subject="Automated Email",
    body="Sent via client credentials",
    to=["recipient@example.com"],
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    sender="user@company.com"  # Must be valid organizational mailbox
)
```

**Token Format:** Standard JWT (starts with `eyJ...`, has 3 parts separated by dots)
**Expiration:** Automatically refreshed by the server
**Permissions:** Application (app acts independently, not as a user)

---

### Comparison Table

| Feature | Personal Accounts | Organizational Accounts |
|---------|------------------|------------------------|
| **Account Type** | @outlook.com, @hotmail.com, @live.com | @company.com (Microsoft 365) |
| **Authentication** | Delegated (user sign-in) | Application (client credentials) |
| **Token Source** | Graph Explorer | Azure AD app registration |
| **Token Format** | Proprietary (`EwB...`) | JWT (`eyJ...`) |
| **Token Lifespan** | 1 hour | Auto-renewed |
| **Best For** | Testing, personal use | Production, automation |
| **Cost** | Free | Requires M365 license (~$6/month) |
| **Setup Complexity** | Simple (2 minutes) | Moderate (15 minutes) |

---

### Single-Tenant Fallback (Optional)

For backwards compatibility, if no credential parameters are provided, the server falls back to environment variables:

- `GRAPH_TENANT_ID`
- `GRAPH_CLIENT_ID`
- `GRAPH_CLIENT_SECRET`
- `GRAPH_DEFAULT_SENDER`
- `GRAPH_USER_ACCESS_TOKEN`

This allows running a single-tenant server where all users share the same Outlook account. **Not recommended for multi-tenant deployments.**

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
