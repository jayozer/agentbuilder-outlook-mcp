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

The MCP server supports two authentication methods. Choose based on your account type:

---

#### Method 1: Personal Microsoft Accounts (@outlook.com, @hotmail.com, @live.com)

**Best for:** Quick testing, personal email automation, individual users

**Steps:**
1. Go to [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer)
2. Sign in with your personal Microsoft account
3. Run any query (e.g., GET /me)
4. Grant `Mail.Send` permission when prompted
5. Click the **"Access token"** tab and copy the token
6. Call the tool:

```python
send_outlook_mail(
    subject="Hello from Personal Account",
    body="This is a test from my @outlook.com account",
    to=["recipient@example.com"],
    access_token="EwBIBMl6BAAU...",  # Your Graph Explorer token
    sender="your.personal@outlook.com"
)
```

**Important Notes:**
- Personal account tokens use Microsoft's proprietary format (starts with `EwB...`)
- This is normal and works correctly - not an error
- Tokens expire after ~1 hour - refresh by getting a new token from Graph Explorer
- No Azure setup required - just sign in to Graph Explorer

---

#### Method 2: Organizational Accounts (Microsoft 365 / Azure AD)

**Best for:** Production applications, automated workflows, enterprise use

**Prerequisites:**
- Azure AD tenant with Microsoft 365
- Exchange Online mailbox
- Azure AD app registration

**Setup:** Follow the complete guide in [AZURE_SETUP.md](./AZURE_SETUP.md)

**Quick Summary:**
1. Create Azure AD app registration in Azure Portal
2. Add `Mail.Send` application permission
3. Grant admin consent
4. Create client secret
5. Call the tool:

```python
send_outlook_mail(
    subject="Automated Email",
    body="Sent from organizational app",
    to=["recipient@example.com"],
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    sender="user@company.com"  # Must be valid organizational mailbox
)
```

**Important Notes:**
- Sender must be a valid Exchange Online mailbox in your tenant
- Tokens auto-refresh (no manual token management needed)
- Requires Microsoft 365 license (~$6/month per mailbox)
- See [AZURE_SETUP.md](./AZURE_SETUP.md) for complete setup instructions

## Troubleshooting

### "Missing credentials" Error

**Problem:** User didn't provide credentials as parameters

**Solution:** Ensure either `access_token` OR (`tenant_id`, `client_id`, `client_secret`) are passed to the tool

**Example:**
```python
# ✓ Correct - provides access_token
send_outlook_mail(..., access_token="EwB...")

# ✓ Correct - provides client credentials
send_outlook_mail(..., tenant_id="...", client_id="...", client_secret="...")

# ✗ Wrong - no credentials provided
send_outlook_mail(..., sender="user@example.com")
```

---

### "JWT is not well formed, there are no dots" Error

**Problem:** This error has TWO possible causes:

**Cause 1:** Server has an invalid `GRAPH_USER_ACCESS_TOKEN` environment variable

**Solution:** Delete the `GRAPH_USER_ACCESS_TOKEN` environment variable from FastMCP dashboard (Environment tab)

**Cause 2:** You're seeing a personal account token format and think it's an error

**Solution:** This is NOT an error! Personal Microsoft account tokens:
- Start with `EwB...` or `EwC...` (not `eyJ...` like JWTs)
- Have zero dots (not 2 dots like JWTs)
- Use Microsoft's proprietary encrypted format
- Work correctly with the Graph API

If your token starts with `EwB` or `EwC`, it's a personal account token and it's working as designed.

---

### "The requested user is invalid" (404)

**Problem:** Trying to send from a mailbox that doesn't exist

**Solutions:**

**For Personal Accounts (@outlook.com):**
- Use `access_token` parameter (delegated flow)
- Do NOT use `tenant_id`/`client_id`/`client_secret` (client credentials don't work with personal accounts)

**For Organizational Accounts:**
- Verify the sender email exists in your Azure AD tenant
- Use the script: `python scripts/check_mailbox.py` to list valid mailboxes
- Ensure the mailbox has an Exchange Online license
- Use the User Principal Name (UPN), e.g., `user@company.onmicrosoft.com`

---

### "The mailbox is either inactive, soft-deleted, or is hosted on-premise" (404)

**Problem:** User exists in Azure AD but has no Exchange Online mailbox

**Solution:**
1. Assign a Microsoft 365 license with Exchange Online to the user
2. Wait 15-30 minutes for mailbox provisioning
3. Verify in Azure Portal → Azure Active Directory → Users → [User] → Licenses

---

### "Access is denied. Check credentials and try again" (401/403)

**Problem:** Permissions not properly configured

**Solution:**
1. Verify `Mail.Send` permission was added in Azure AD app registration
2. Ensure admin consent was granted (green checkmark in API permissions)
3. For client credentials: Use **Application permissions** (not Delegated)
4. For personal accounts: Use **Delegated permissions** and get token from Graph Explorer
5. Wait a few minutes for permission changes to propagate

---

### Token Expiration

**Problem:** Delegated tokens (from Graph Explorer) expire after ~1 hour

**Symptoms:**
- Error: "Access token has expired"
- Error: "Invalid authentication token"

**Solutions:**
- **For testing:** Get a fresh token from Graph Explorer
- **For production:** Use client credentials flow (tokens auto-refresh)

**How to get a fresh token:**
1. Go back to Graph Explorer
2. Run any query
3. Copy the new token from "Access token" tab
4. Use the new token in your MCP client

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
