"""Test if the access token works directly with Graph API."""
import os
import httpx


def test_token():
    token = os.environ.get("GRAPH_USER_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("GRAPH_USER_ACCESS_TOKEN not set")

    headers = {"Authorization": f"Bearer {token}"}

    print(f"Token format: {token[:30]}...")
    print(f"Token length: {len(token)}")
    print(f"Number of dots: {token.count('.')}\n")

    # Test 1: Get user profile
    print("Test 1: GET /me")
    try:
        response = httpx.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers,
            timeout=10.0
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Success! User: {data.get('displayName')} ({data.get('userPrincipalName')})")
        else:
            print(f"  ✗ Error: {response.text}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")

    # Test 2: Send email
    print("\nTest 2: POST /me/sendMail (dry-run via mailFolders)")
    try:
        response = httpx.get(
            "https://graph.microsoft.com/v1.0/me/mailFolders",
            headers=headers,
            timeout=10.0
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ Can access mailbox")
        else:
            print(f"  ✗ Error: {response.text}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")

    # Test 3: Check token permissions
    print("\nTest 3: Try to send actual email")
    try:
        payload = {
            "message": {
                "subject": "Test from Python",
                "body": {
                    "contentType": "Text",
                    "content": "Testing direct API call"
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": "jayozer@gmail.com"
                        }
                    }
                ]
            },
            "saveToSentItems": "true"
        }
        response = httpx.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers=headers,
            json=payload,
            timeout=10.0
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 202:
            print(f"  ✓ Email sent successfully!")
        else:
            print(f"  ✗ Error: {response.text}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")


if __name__ == "__main__":
    test_token()
