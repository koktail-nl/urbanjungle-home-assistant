"""UrbanJungle Care API client.

Talks to the same backend as the mobile and Homey apps. Endpoints and payloads
mirror apps/homey/api/UrbanJungleCareApi.ts. Authentication is delegated to the
auth object it is given, which hands out a bearer token.
"""
import json as jsonlib
import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientError, ClientSession, ClientTimeout

from .oauth_auth import OAuth2Auth, OAuth2TokenError
from ..const import DEFAULT_API_URL

_LOGGER = logging.getLogger(__name__)

_REQUEST_TIMEOUT = ClientTimeout(total=60)


class ApiError(Exception):
    """A backend request failed."""


class UrbanJungleCareApi:
    """Async client for the UrbanJungle Care backend."""

    def __init__(
        self,
        session: ClientSession,
        auth: OAuth2Auth,
        base_url: str = DEFAULT_API_URL,
    ) -> None:
        """Initialize with an aiohttp session, an auth handler and the API base URL."""
        self._session = session
        self._auth = auth
        self.base_url = base_url.rstrip("/")

    @property
    def auth(self) -> OAuth2Auth:
        """Return the auth handler."""
        return self._auth

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Any] = None,
    ) -> Any:
        """Make an authenticated request, refreshing the token once on 401/403.

        Returns the decoded JSON body, or ``None`` for 404/empty responses.

        Raises:
            OAuth2TokenError: if the token cannot be (re)obtained (needs re-auth).
            ApiError: on any other backend error.
        """
        url = f"{self.base_url}{path}"
        try:
            token = await self._auth.async_get_token()
            response = await self._send(method, url, token, json)

            if response[0] in (401, 403):
                _LOGGER.debug("Got %s for %s %s, refreshing token", response[0], method, path)
                self._auth.async_invalidate()
                token = await self._auth.async_get_token()
                response = await self._send(method, url, token, json)

            status, body = response
            return self._handle(status, body, method, path)
        except ClientError as err:
            raise ApiError(f"Network error during {method} {path}: {err}") from err

    async def _send(self, method: str, url: str, token: str, json: Optional[Any]):
        """Send one request and return (status, text_body)."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        async with self._session.request(
            method, url, headers=headers, json=json, timeout=_REQUEST_TIMEOUT
        ) as resp:
            return resp.status, await resp.text()

    @staticmethod
    def _handle(status: int, body: str, method: str, path: str) -> Any:
        """Turn a (status, body) pair into a result.

        HTTP errors are tolerated (return ``None``) like the Homey client so a
        single failing endpoint does not break the whole update. Genuine auth
        failures surface earlier via ``OAuth2TokenError`` (triggering reauth),
        and network errors raise ``ApiError`` in ``_request``.
        """
        if status == 429:
            # Rate limited: the backend stored what it could; not an error.
            _LOGGER.debug("%s %s throttled (429)", method, path)
            return None
        if status >= 400:
            if status != 404:
                _LOGGER.warning("%s %s -> %s: %s", method, path, status, body[:200])
            return None
        if not body:
            return None
        try:
            return jsonlib.loads(body)
        except ValueError:
            return None

    # --- Users -------------------------------------------------------------

    async def get_profile(self) -> Optional[Dict[str, Any]]:
        """GET /api/users/profile."""
        return await self._request("GET", "/api/users/profile")

    async def get_subscription(self) -> Optional[Dict[str, Any]]:
        """GET /api/users/subscription. Returns ``None`` when not subscribed."""
        return await self._request("GET", "/api/users/subscription")

    # --- Devices -----------------------------------------------------------

    async def get_devices(self) -> List[Dict[str, Any]]:
        """GET /api/devices."""
        return await self._request("GET", "/api/devices") or []

    async def add_device_metrics(
        self, device_id: str, metrics: List[Dict[str, Any]]
    ) -> Any:
        """POST /api/devices/{device_id}/metrics."""
        return await self._request(
            "POST", f"/api/devices/{device_id}/metrics", json=metrics
        )

    async def add_device_entity(self, device: Dict[str, Any]) -> Any:
        """POST /api/devices."""
        return await self._request("POST", "/api/devices", json=device)

    # --- Plants ------------------------------------------------------------

    async def get_plants(self) -> List[Dict[str, Any]]:
        """GET /api/plants."""
        return await self._request("GET", "/api/plants") or []

    # --- Integrations ------------------------------------------------------

    async def get_integration(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """GET /api/integrations/{id}."""
        return await self._request("GET", f"/api/integrations/{integration_id}")

    async def post_integration(self, integration: Dict[str, Any]) -> Any:
        """POST /api/integrations/{id} (create or update)."""
        return await self._request(
            "POST", f"/api/integrations/{integration['id']}", json=integration
        )

    async def delete_integration(self, integration_id: str) -> Any:
        """DELETE /api/integrations/{id}."""
        return await self._request("DELETE", f"/api/integrations/{integration_id}")
