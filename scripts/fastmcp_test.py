from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

from fastmcp.client import Client


FASTMCP_URL = "https://agentbuilder-outlook-mcp.fastmcp.app/mcp"
DEFAULT_SUBJECT = "FastMCP Remote Test"
DEFAULT_BODY = "This is a dry-run request issued from scripts/fastmcp_test.py."
DEFAULT_TO = ["jayozer@gmail.com"]
DEFAULT_SENDER = os.environ.get("GRAPH_DEFAULT_SENDER", "jayozer@outlook.com")  # Override via env var


def build_payload_delegated(access_token: str, dry_run: bool = False) -> Dict[str, Any]:
    """Build tool arguments using delegated access token."""
    return {
        "subject": DEFAULT_SUBJECT,
        "body": DEFAULT_BODY,
        "to": DEFAULT_TO,
        "sender": DEFAULT_SENDER,
        "access_token": access_token,
        "dry_run": dry_run,
        "save_to_sent_items": True,
    }


def build_payload_client_creds() -> Dict[str, Any]:
    """Build tool arguments using client credentials flow."""
    tenant_id = os.environ.get("GRAPH_TENANT_ID")
    client_id = os.environ.get("GRAPH_CLIENT_ID")
    client_secret = os.environ.get("GRAPH_CLIENT_SECRET")

    if not all([tenant_id, client_id, client_secret]):
        raise RuntimeError(
            "For client credentials, set: GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET"
        )

    return {
        "subject": DEFAULT_SUBJECT,
        "body": DEFAULT_BODY,
        "to": DEFAULT_TO,
        "sender": DEFAULT_SENDER,
        "tenant_id": tenant_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "dry_run": False,  # Real send!
        "save_to_sent_items": True,
    }


async def run_test() -> None:
    # Try client credentials first, fall back to delegated token
    try:
        payload = build_payload_client_creds()
        print("Testing with CLIENT CREDENTIALS flow...")
    except RuntimeError:
        token = os.environ.get("GRAPH_USER_ACCESS_TOKEN")
        if not token:
            raise RuntimeError(
                "Set either:\n"
                "  - GRAPH_USER_ACCESS_TOKEN (delegated token)\n"
                "  - GRAPH_TENANT_ID + GRAPH_CLIENT_ID + GRAPH_CLIENT_SECRET (client credentials)"
            )
        payload = build_payload_delegated(token, dry_run=False)  # REAL SEND!
        print("Testing with DELEGATED TOKEN flow...")

    # MCP server is Open auth, no authentication needed to connect
    async with Client(FASTMCP_URL) as client:
        # Pass arguments as a dict, not kwargs
        response = await client.call_tool("send_outlook_mail", arguments=payload)
        print("Remote MCP response:")
        print(response)


def main() -> None:
    asyncio.run(run_test())


if __name__ == "__main__":
    main()
