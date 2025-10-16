# Azure AD App Registration Setup Guide

Complete step-by-step guide for configuring Azure AD to work with the Outlook MCP Server.

## Prerequisites

- Azure account (free tier works)
- Access to Azure Portal (https://portal.azure.com)
- For organizational accounts: Microsoft 365 subscription with Exchange Online

---

## Part 1: Create App Registration

### Step 1: Navigate to App Registrations

1. Go to https://portal.azure.com
2. Search for **"App registrations"** in the top search bar
3. Click **"App registrations"** from the results
4. Click **"+ New registration"** button

### Step 2: Configure Basic Settings

**Name:** `Outlook MCP Mailer` (or any descriptive name)

**Supported account types:** Choose based on your needs:
- **Single tenant**: Only your organization → Choose if you only need organizational accounts
- **Multitenant**: Any Azure AD directory → Choose for broader compatibility
- **Multitenant + Personal**: Any directory AND personal Microsoft accounts → **Recommended** for maximum flexibility

**Redirect URI:** Leave blank (not needed for this use case)

Click **"Register"**

### Step 3: Save Your Credentials

After registration, you'll see the **Overview** page. Copy these values:

```
Application (client) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Directory (tenant) ID: yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
```

**Save these somewhere safe** - you'll need them later.

---

## Part 2: Configure API Permissions

### Step 4: Add Microsoft Graph Permissions

1. In the left sidebar, click **"API permissions"**
2. Click **"+ Add a permission"**
3. Select **"Microsoft Graph"** (should be the first tile)

### For Organizational Accounts (Client Credentials Flow)

4. Choose **"Application permissions"**
   - This allows your app to act independently without a signed-in user
5. Expand **"Mail"** section (or search for "mail")
6. Check the box for **"Mail.Send"**
   - Description: "Send mail as any user"
7. Click **"Add permissions"** at the bottom

### For Personal Accounts (Optional - Delegated Flow)

If you want to support personal Microsoft accounts:

8. Click **"+ Add a permission"** again
9. Select **"Microsoft Graph"**
10. This time, choose **"Delegated permissions"**
11. Search for and select **"Mail.Send"** (delegated)
12. Click **"Add permissions"**

### Step 5: Grant Admin Consent

**Critical step!** Your permissions won't work without this.

1. Back on the **API permissions** page, look for the button:
   - **"Grant admin consent for [Your Tenant Name]"**
2. Click this button
3. Confirm by clicking **"Yes"** in the dialog

**Verification:** After granting consent, you should see:
- Green checkmarks (✓) in the "Status" column
- Text showing "Granted for [Your Tenant]"

---

## Part 3: Create Client Secret

### Step 6: Generate Secret

1. In the left sidebar, click **"Certificates & secrets"**
2. Click the **"Client secrets"** tab
3. Click **"+ New client secret"**

**Description:** `MCP Outlook Mailer Secret` (or any descriptive name)

**Expires:** Choose your preference:
- **180 days (6 months)**: Good for testing
- **730 days (24 months)**: Recommended for production
- **Custom**: Set your own expiration date

4. Click **"Add"**

### Step 7: Copy the Secret Value

**⚠️ CRITICAL - DO THIS IMMEDIATELY!**

After clicking Add, you'll see the secret with two fields:
- **Secret ID**: (you don't need this)
- **Value**: `Abc~123xyz...` ← **COPY THIS NOW!**

**This is your only chance to see the value.** Once you navigate away, you can never retrieve it again. If you lose it, you'll have to create a new secret.

**Save it securely** - treat this like a password.

---

## Part 4: Verify Mailbox (For Organizational Accounts)

### Step 8: Check Available Mailboxes

If using client credentials (organizational accounts), you need a valid mailbox.

**Option A: Use the check_mailbox script**

```bash
# Set your credentials
export GRAPH_TENANT_ID="your-tenant-id"
export GRAPH_CLIENT_ID="your-client-id"
export GRAPH_CLIENT_SECRET="your-client-secret"

# Run the mailbox checker
python scripts/check_mailbox.py
```

This will list all mailboxes available in your tenant.

**Option B: Check manually in Azure Portal**

1. Go to **Azure Active Directory** → **Users**
2. Find your user account
3. Look for **"User principal name"** (e.g., `user@company.onmicrosoft.com`)
4. Verify the user has an Exchange Online mailbox

### Step 9: Grant Mailbox Permissions (If Needed)

If you want to send from a specific mailbox, ensure:
- The mailbox has an active Exchange Online license
- The mailbox is not disabled or soft-deleted
- You're using the correct User Principal Name (UPN)

---

## Part 5: Test Your Setup

### Test 1: With Client Credentials (Organizational)

```bash
# Set environment variables
export GRAPH_TENANT_ID="your-tenant-id"
export GRAPH_CLIENT_ID="your-client-id"
export GRAPH_CLIENT_SECRET="your-client-secret"
export GRAPH_DEFAULT_SENDER="user@company.com"

# Run the test
python scripts/fastmcp_test.py
```

Expected output:
```
Testing with CLIENT CREDENTIALS flow...
Remote MCP response: Microsoft Graph accepted the message for 1 recipient(s).
```

### Test 2: With Personal Account (Delegated)

```bash
# Get token from Graph Explorer
# https://developer.microsoft.com/graph/graph-explorer

export GRAPH_USER_ACCESS_TOKEN="your-token-from-graph-explorer"
export GRAPH_DEFAULT_SENDER="your@outlook.com"

# Unset client credentials to force delegated flow
unset GRAPH_TENANT_ID
unset GRAPH_CLIENT_ID
unset GRAPH_CLIENT_SECRET

# Run the test
python scripts/fastmcp_test.py
```

Expected output:
```
Testing with DELEGATED TOKEN flow...
Remote MCP response: Microsoft Graph accepted the message for 1 recipient(s).
```

---

## Summary: What You Need

### For Client Credentials (Organizational Accounts)

**From Azure:**
- `GRAPH_TENANT_ID` - Directory (tenant) ID from app registration
- `GRAPH_CLIENT_ID` - Application (client) ID from app registration
- `GRAPH_CLIENT_SECRET` - Client secret value (from Certificates & secrets)
- Valid organizational mailbox (user@company.com)

**Permissions:**
- Mail.Send (Application permission)
- Admin consent granted

### For Delegated Flow (Personal Accounts)

**From Graph Explorer:**
- `GRAPH_USER_ACCESS_TOKEN` - Access token from Graph Explorer
- Personal Microsoft account (@outlook.com, @hotmail.com, @live.com)

**Permissions:**
- Mail.Send (Delegated permission)
- User consent during Graph Explorer sign-in

---

## Troubleshooting

### "The requested user is invalid" (404)

**Problem:** Trying to send from a non-existent or personal mailbox with client credentials

**Solution:**
- Verify the sender email exists in your Azure AD tenant
- Use `python scripts/check_mailbox.py` to list valid mailboxes
- Personal accounts cannot use client credentials - use delegated flow instead

### "The mailbox is either inactive, soft-deleted, or is hosted on-premise" (404)

**Problem:** User exists in Azure AD but has no Exchange Online mailbox

**Solution:**
- Assign a Microsoft 365 license with Exchange Online
- Wait 15-30 minutes for mailbox provisioning
- Verify in Azure AD → Users → [User] → Licenses

### "Access is denied. Check credentials and try again" (401/403)

**Problem:** Permissions not properly configured or consent not granted

**Solution:**
- Verify Mail.Send permission was added
- Ensure admin consent was granted (green checkmark in API permissions)
- Check that you're using Application permissions (not Delegated) for client credentials
- Wait a few minutes for permission changes to propagate

### "JWT is not well formed, there are no dots" (401)

**Problem:** Using a personal account token format with client credentials flow

**Solution:**
- This error occurs when mixing authentication methods
- Personal accounts produce non-JWT tokens (starting with `EwB...`) - this is normal
- Use `access_token` parameter (delegated flow) for personal accounts
- Use `tenant_id`/`client_id`/`client_secret` (client credentials) for organizational accounts

### "Invalid client secret" (401)

**Problem:** Wrong client secret or it expired

**Solution:**
- Verify you copied the secret **value**, not the secret ID
- Check if the secret has expired (Certificates & secrets page)
- Create a new secret if needed

---

## Security Best Practices

1. **Never commit credentials to git**
   - Use `.env` files (already in `.gitignore`)
   - Use environment variables or secure vaults

2. **Rotate secrets regularly**
   - Set reasonable expiration dates
   - Create new secrets before old ones expire
   - Delete unused/expired secrets

3. **Use least privilege**
   - Only grant `Mail.Send` permission (don't add unnecessary permissions)
   - Use application permissions only when needed

4. **Monitor usage**
   - Review sign-in logs in Azure AD
   - Check for unusual activity
   - Set up alerts for high-volume API usage

5. **Separate dev/prod**
   - Use different app registrations for development and production
   - Don't share production credentials with developers

---

## Additional Resources

- [Microsoft Graph Mail API](https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [Azure AD App Registration](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer)
- [Microsoft Graph Permissions Reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
