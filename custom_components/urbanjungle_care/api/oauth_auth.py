"""OAuth2 authentication for the UrbanJungle Care API.

Wraps Home Assistant's :class:`OAuth2Session`, which keeps the access token fresh and
writes a rotated refresh token back into the config entry. The API client only needs a
bearer token and a way to force a new one after a 401, which is what this exposes.
"""
import logging
from typing import Any, Dict

from homeassistant.helpers import config_entry_oauth2_flow

_LOGGER = logging.getLogger(__name__)


class OAuth2TokenError(Exception):
    """The access token could not be obtained or refreshed; the user must re-authorize."""


class OAuth2Auth:
    """Hands out the access token of one config entry."""

    def __init__(self, session: config_entry_oauth2_flow.OAuth2Session) -> None:
        """Initialize with the session Home Assistant manages for this entry."""
        self._session = session
        self._force_refresh = False

    @property
    def token(self) -> Dict[str, Any]:
        """Return the stored token, as Home Assistant keeps it in the config entry."""
        return self._session.token

    async def async_get_token(self) -> str:
        """Return a valid access token, refreshing it when needed."""
        try:
            if self._force_refresh:
                self._force_refresh = False
                await self._async_refresh()
            else:
                await self._session.async_ensure_token_valid()
        except Exception as err:  # noqa: BLE001
            raise OAuth2TokenError(f"Could not refresh the access token: {err}") from err

        token = self._session.token.get("access_token")
        if not token:
            raise OAuth2TokenError("The stored token carries no access token")
        return token

    def async_invalidate(self) -> None:
        """Make the next call refresh the token, after the backend rejected the current one."""
        self._force_refresh = True

    async def _async_refresh(self) -> None:
        """Trade the refresh token for a new access token and store the result.

        Home Assistant only refreshes once the stored token says it expired. A token the
        backend rejects earlier than that needs this push, and the new token is written back
        the same way Home Assistant does it, so a rotated refresh token survives a restart.
        """
        session = self._session
        new_token = await session.implementation.async_refresh_token(session.token)
        session.hass.config_entries.async_update_entry(
            session.config_entry,
            data={**session.config_entry.data, "token": new_token},
        )
