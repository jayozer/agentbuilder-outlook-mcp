# FastMCP Dashboard Configuration Guide

## Multi-Tenant Setup Instructions

Follow these steps to configure your FastMCP deployment for multi-tenant usage.

### 1. Environment Tab

**IMPORTANT:** For multi-tenant operation, DELETE or leave EMPTY all environment variables:

```
GRAPH_TENANT_ID = (delete or leave empty)
GRAPH_CLIENT_ID = (delete or leave empty)
GRAPH_CLIENT_SECRET = (delete or leave empty)
GRAPH_DEFAULT_SENDER = (delete or leave empty)
GRAPH_USER_ACCESS_TOKEN = (delete or leave empty)
```

**Why?** In multi-tenant mode, each user provides their own credentials as tool parameters. The server should NOT store any credentials.

### 2. Security Tab

**Authentication Mode:** `Open`

**Discoverable on Registry:** `ON` (if you want it publicly listed)

**Why Open?** The MCP server itself doesn't need authentication because credential-based isolation happens at the tool level. Each user provides their own Microsoft credentials when calling `send_outlook_mail`.

### 3. General Tab

Keep the existing configuration:
- **Project Name:** `agentbuilder-outlook-mcp`
- **Entrypoint:** `server.py:mcp`
- **Requirements File:** `pyproject.toml`

### 4. Deploy Changes

After making these changes:
1. Save the configuration
2. Redeploy the server (if auto-deploy is not enabled)
3. Wait for deployment to complete

### 5. Test the Deployment

Use the test script with your own Graph Explorer token:

```bash
# Set your token
export GRAPH_USER_ACCESS_TOKEN="your-token-from-graph-explorer"

# Run the test
python scripts/fastmcp_test.py
```

Or test manually via MCP client:

```python
send_outlook_mail(
    subject="Multi-Tenant Test",
    body="Testing with my credentials",
    to=["your.email@example.com"],
    access_token="EwBIBMl6BAAU...",  # Your Graph Explorer token
    sender="your.email@example.com",
    dry_run=True  # Safe test mode
)
```

## Verification Checklist

- [ ] Environment variables are empty/deleted on FastMCP
- [ ] Security mode is set to "Open"
- [ ] Server redeployed successfully
- [ ] Test with access_token parameter works
- [ ] No server-side credential errors in logs

## User Instructions

Share these instructions with users who want to connect to your MCP server:

### Connecting to the Server

Add to your MCP client configuration (`mcp.json` or similar):

```json
{
  "mcpServers": {
    "outlook-mailer": {
      "url": "https://agentbuilder-outlook-mcp.fastmcp.app/mcp"
    }
  }
}
```

### Using the Tool

**Option 1: With Graph Explorer Token (Quick Test)**

1. Go to [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer)
2. Sign in with your Microsoft account
3. Grant `Mail.Send` permission
4. Copy your access token
5. Call the tool:

```python
send_outlook_mail(
    subject="Hello",
    body="This is a test",
    to=["recipient@example.com"],
    access_token="YOUR_TOKEN_HERE",
    sender="your.email@example.com"
)
```

**Option 2: With Azure AD App Registration (Production)**

1. Create an Azure AD app registration
2. Grant `Mail.Send` application permission
3. Create a client secret
4. Call the tool:

```python
send_outlook_mail(
    subject="Automated Email",
    body="Sent from my app",
    to=["recipient@example.com"],
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    sender="mailbox@example.com"
)
```

## Troubleshooting

### "Missing credentials" Error

**Problem:** User didn't provide credentials as parameters

**Solution:** Ensure either `access_token` OR (`tenant_id`, `client_id`, `client_secret`) are passed to the tool

### "JWT is not well formed" Error

**Problem:** Server has invalid `GRAPH_USER_ACCESS_TOKEN` environment variable

**Solution:** Delete the `GRAPH_USER_ACCESS_TOKEN` environment variable from FastMCP dashboard

### Token Expiration

**Problem:** Delegated tokens expire after ~1 hour

**Solution:**
- For testing: Get a fresh token from Graph Explorer
- For production: Use client credentials flow (doesn't expire)

## Architecture Notes

### Multi-Tenant vs Single-Tenant

**Multi-Tenant (Current Setup):**
- Each user provides their own credentials
- Server stores NO credentials
- Each user sends from their own Outlook account
- True SaaS model

**Single-Tenant (Alternative):**
- Set environment variables on FastMCP
- All users share the same Outlook account
- Simpler but less flexible
- Not recommended for public servers
