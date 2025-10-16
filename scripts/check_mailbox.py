"""
Quick script to check what mailbox your Azure AD app can access.
"""
import os
import httpx


def get_access_token():
    """Get token using client credentials."""
    tenant_id = os.environ.get("GRAPH_TENANT_ID")
    client_id = os.environ.get("GRAPH_CLIENT_ID")
    client_secret = os.environ.get("GRAPH_CLIENT_SECRET")

    if not all([tenant_id, client_id, client_secret]):
        raise RuntimeError("Set GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET")

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default",
    }

    response = httpx.post(url, data=data, timeout=15.0)
    response.raise_for_status()
    return response.json()["access_token"]


def list_users(token):
    """List users in the tenant."""
    url = "https://graph.microsoft.com/v1.0/users"
    headers = {"Authorization": f"Bearer {token}"}

    response = httpx.get(url, headers=headers, timeout=20.0)
    response.raise_for_status()
    return response.json()


def main():
    print("Getting access token...")
    token = get_access_token()
    print("✓ Token acquired\n")

    print("Fetching users in your Azure AD tenant...")
    users = list_users(token)

    print(f"\nFound {len(users.get('value', []))} users:\n")

    for user in users.get('value', []):
        upn = user.get('userPrincipalName', 'N/A')
        display_name = user.get('displayName', 'N/A')
        mail = user.get('mail', 'N/A')
        print(f"  • {display_name}")
        print(f"    Email: {mail}")
        print(f"    UPN: {upn}\n")

    if users.get('value'):
        print("\n💡 Use one of these User Principal Names (UPN) as the 'sender' parameter.")
    else:
        print("\n⚠️  No users found. You may need 'User.Read.All' permission.")


if __name__ == "__main__":
    main()
