"""Config flow for UrbanJungle Care integration.

The user authorizes Home Assistant in their UrbanJungle account and comes back with a
token; Home Assistant handles the authorization redirect and the PKCE exchange.
"""
import logging
import socket
import uuid
from typing import Any, Dict

from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow, instance_id
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import async_register_implementation
from .api import UrbanJungleCareApi
from .const import (
    CONF_API_URL,
    CONF_INTEGRATION_ID,
    CONF_USER_ID,
    DEFAULT_API_URL,
    DOMAIN,
    INTEGRATION_NAME,
    INTEGRATION_TYPE,
    OAUTH_SCOPES,
)

_LOGGER = logging.getLogger(__name__)


def _get_local_ip() -> str:
    """Best-effort local IP address (Homey uses 'unknown' as fallback)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "unknown"
    finally:
        sock.close()


class _EntryToken:
    """Carries a freshly granted token to the API client before an entry exists.

    The config flow has to call the backend to register the integration, which happens
    before there is a config entry for :class:`OAuth2Session` to read from.
    """

    def __init__(self, token: Dict[str, Any]) -> None:
        self._token = token

    async def async_get_token(self) -> str:
        return self._token["access_token"]

    def async_invalidate(self) -> None:
        """A token this fresh is not worth refreshing; a failure surfaces as an error."""


class UrbanJungleCareConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle the OAuth2 config flow for UrbanJungle Care."""

    VERSION = 3
    DOMAIN = DOMAIN

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start the flow, making sure the OAuth2 client is registered."""
        async_register_implementation(self.hass)
        return await super().async_step_user(user_input)

    @property
    def logger(self) -> logging.Logger:
        """Return the logger the OAuth2 helper writes to."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> Dict[str, Any]:
        """Extra data to append to the authorize URL."""
        return {"scope": " ".join(OAUTH_SCOPES)}

    async def async_step_reauth(self, entry_data: Dict[str, Any]) -> ConfigFlowResult:
        """Re-authorize when the refresh token is no longer accepted."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authorization, then run the same authorize step as a fresh setup."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: Dict[str, Any]) -> ConfigFlowResult:
        """Register this Home Assistant as an integration and store the entry."""
        session = async_get_clientsession(self.hass)
        api_url = DEFAULT_API_URL
        if self.source == "reauth" and self._get_reauth_entry() is not None:
            api_url = self._get_reauth_entry().data.get(CONF_API_URL, DEFAULT_API_URL)

        api = UrbanJungleCareApi(session, _EntryToken(data["token"]), api_url)

        profile = await api.get_profile() or {}
        subject_id = await instance_id.async_get(self.hass)
        user_id = profile.get("uid") or profile.get("id") or subject_id

        if self.source == "reauth":
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data_updates=data
            )

        await self.async_set_unique_id(user_id)
        self._abort_if_unique_id_configured()

        integration_id = str(uuid.uuid4())
        ip_address = await self.hass.async_add_executor_job(_get_local_ip)
        await api.post_integration(
            {
                "id": integration_id,
                "subjectId": subject_id,
                "name": INTEGRATION_NAME,
                "ipAddress": ip_address,
                "type": INTEGRATION_TYPE,
                "devices": [],
            }
        )

        title = profile.get("email") or profile.get("name") or INTEGRATION_NAME
        return self.async_create_entry(
            title=f"UrbanJungle ({title})",
            data={
                **data,
                CONF_USER_ID: user_id,
                CONF_INTEGRATION_ID: integration_id,
                CONF_API_URL: api_url,
            },
        )
