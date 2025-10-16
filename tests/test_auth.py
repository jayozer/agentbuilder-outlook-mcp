import pytest
import httpx

from mcp_outlook.auth import GraphAuthError, GraphTokenManager
from mcp_outlook.config import GraphSettings


def test_get_token_uses_delegated_when_available():
    settings = GraphSettings(
        tenant_id=None,
        client_id=None,
        client_secret=None,
        delegated_token="delegated-token",
    )
    manager = GraphTokenManager(settings)

    assert manager.get_token() == "delegated-token"


def test_client_credentials_token_fetch_and_cache():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        assert request.url.path.endswith("/oauth2/v2.0/token")
        return httpx.Response(
            200,
            json={"access_token": "cached-token", "expires_in": 3600},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)

    settings = GraphSettings(
        tenant_id="tenant",
        client_id="client",
        client_secret="secret",
    )

    manager = GraphTokenManager(
        settings,
        client=client,
        clock_skew_buffer=0.0,
    )

    assert manager.get_token() == "cached-token"
    assert manager.get_token() == "cached-token"
    assert calls["count"] == 1

    client.close()


def test_missing_client_credentials_config_raises():
    settings = GraphSettings(
        tenant_id=None,
        client_id=None,
        client_secret=None,
    )
    manager = GraphTokenManager(settings)

    with pytest.raises(GraphAuthError):
        manager.get_token()
