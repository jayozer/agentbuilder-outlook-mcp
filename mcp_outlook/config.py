from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from typing import Optional


class ConfigurationError(RuntimeError):
    """Raised when required Microsoft Graph configuration is missing."""


@dataclass(frozen=True)
class GraphSettings:
    tenant_id: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    default_sender: Optional[str] = None
    delegated_token: Optional[str] = None

    @classmethod
    def load(cls) -> "GraphSettings":
        tenant_id = os.environ.get("GRAPH_TENANT_ID", "").strip() or None
        client_id = os.environ.get("GRAPH_CLIENT_ID", "").strip() or None
        client_secret = os.environ.get("GRAPH_CLIENT_SECRET", "").strip() or None
        default_sender = os.environ.get("GRAPH_DEFAULT_SENDER", "").strip() or None
        delegated_token = os.environ.get("GRAPH_USER_ACCESS_TOKEN", "").strip() or None

        missing = [
            name
            for name, value in [
                ("GRAPH_TENANT_ID", tenant_id),
                ("GRAPH_CLIENT_ID", client_id),
                ("GRAPH_CLIENT_SECRET", client_secret),
            ]
            if not value
        ]
        if missing and not delegated_token:
            raise ConfigurationError(
                "Missing Microsoft Graph configuration variables: "
                + ", ".join(missing)
            )

        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            default_sender=default_sender,
            delegated_token=delegated_token,
        )


@lru_cache(maxsize=1)
def get_graph_settings() -> GraphSettings:
    """
    Retrieve cached Microsoft Graph settings.

    Raises:
        ConfigurationError: if required environment variables are missing.
    """
    return GraphSettings.load()
