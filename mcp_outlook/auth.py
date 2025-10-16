from __future__ import annotations

import time
from typing import Optional

import httpx
import logging

from .config import GraphSettings


class GraphAuthError(RuntimeError):
    """Raised when acquiring a Microsoft Graph token fails."""


class GraphTokenManager:
    """
    Manage Microsoft Graph access tokens.

    The manager prefers a delegated token when provided. Otherwise, it issues
    client-credential tokens and caches them until shortly before expiry.
    """

    def __init__(
        self,
        settings: Optional[GraphSettings] = None,
        *,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        http_timeout: float = 15.0,
        clock_skew_buffer: float = 60.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        # Priority: constructor parameters > settings > None
        # This enables multi-tenant usage where credentials come from tool parameters
        self._tenant_id = tenant_id or (settings.tenant_id if settings else None)
        self._client_id = client_id or (settings.client_id if settings else None)
        self._client_secret = client_secret or (settings.client_secret if settings else None)
        self._delegated_token = access_token or (settings.delegated_token if settings else None)

        self._http_timeout = http_timeout
        self._clock_skew_buffer = clock_skew_buffer
        self._client = client
        self._token: Optional[str] = None
        self._expiry: float = 0.0
        self._logger = logging.getLogger("mcp_outlook.auth")

    def get_token(self) -> str:
        """
        Return a valid access token for Microsoft Graph.

        Returns:
            str: a bearer token string suitable for the Authorization header.

        Raises:
            GraphAuthError: when token acquisition fails.
        """
        if self._delegated_token:
            self._logger.debug("Using delegated Microsoft Graph token.")
            return self._delegated_token

        if self._token and (time.time() + self._clock_skew_buffer) < self._expiry:
            self._logger.debug("Reusing cached Microsoft Graph token.")
            return self._token

        token, expiry = self._request_client_credentials_token()
        self._token = token
        self._expiry = expiry
        self._logger.info("Fetched new Microsoft Graph access token.")
        return token

    def _request_client_credentials_token(self) -> tuple[str, float]:
        if not (self._tenant_id and self._client_id and self._client_secret):
            raise GraphAuthError(
                "Client credential flow requires tenant_id, client_id, "
                "and client_secret to be provided either as parameters or environment variables."
            )

        url = (
            f"https://login.microsoftonline.com/{self._tenant_id}"
            "/oauth2/v2.0/token"
        )
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }

        try:
            response = (
                self._client.post(url, data=data, timeout=self._http_timeout)
                if self._client
                else httpx.post(url, data=data, timeout=self._http_timeout)
            )
        except httpx.HTTPError as exc:
            self._logger.error("Error contacting token endpoint: %s", exc)
            raise GraphAuthError(
                f"Failed to contact Microsoft identity platform: {exc}"
            ) from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text
            self._logger.error(
                "Token endpoint returned %s: %s", response.status_code, detail
            )
            raise GraphAuthError(
                f"Token endpoint returned {response.status_code}: {detail}"
            ) from exc

        payload = response.json()
        token = payload.get("access_token")
        expires_in = payload.get("expires_in")

        if not token or not expires_in:
            raise GraphAuthError("Token response missing access_token or expires_in.")

        expiry = time.time() + float(expires_in)
        return token, expiry
