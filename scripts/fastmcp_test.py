from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

from fastmcp.client import BearerAuth, Client


FASTMCP_URL = "https://agentbuilder-outlook-mcp.fastmcp.app/mcp"
DEFAULT_SUBJECT = "FastMCP Remote Test"
DEFAULT_BODY = "This is a dry-run request issued from scripts/fastmcp_test.py."
DEFAULT_TO = ["jayozer@gmail.com"]
DEFAULT_SENDER = "jayozer@outlook.com"


def build_payload() -> Dict[str, Any]:
    return {
        "subject": DEFAULT_SUBJECT,
        "body": DEFAULT_BODY,
        "to": DEFAULT_TO,
        "sender": DEFAULT_SENDER,
        "dry_run": True,
        "save_to_sent_items": True,
    }


async def run_test() -> None:
    token = os.environ.get("GRAPH_USER_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("GRAPH_USER_ACCESS_TOKEN must be set in the environment.")

    auth = BearerAuth(token)
    payload = build_payload()

    async with Client(FASTMCP_URL, auth=auth) as client:
        response = await client.call_tool("send_outlook_mail", **payload)
        print("Remote MCP response:")
        print(response)


def main() -> None:
    asyncio.run(run_test())


if __name__ == "__main__":
    main()
