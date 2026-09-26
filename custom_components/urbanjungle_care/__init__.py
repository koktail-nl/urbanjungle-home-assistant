"""UrbanJungle Care integration for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import OAuth2Auth, UrbanJungleCareApi
from .const import (
    CONF_API_URL,
    CONF_INTEGRATION_ID,
    DEFAULT_API_URL,
    DOMAIN,
    OAUTH_AUTHORIZE_PATH,
    OAUTH_CLIENT_ID,
    OAUTH_TOKEN_PATH,
)
from .coordinator import UrbanJungleCareCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


@callback
def async_register_implementation(
    hass: HomeAssistant, api_url: str = DEFAULT_API_URL
) -> None:
    """Register the OAuth2 client the config flow authorizes with.

    The config flow calls this as well: a first install has no config entry yet, so the
    component itself has not been set up at the moment the user starts the flow.
    """
    config_entry_oauth2_flow.async_register_implementation(
        hass,
        DOMAIN,
        config_entry_oauth2_flow.LocalOAuth2ImplementationWithPkce(
            hass,
            DOMAIN,
            OAUTH_CLIENT_ID,
            f"{api_url}{OAUTH_AUTHORIZE_PATH}",
            f"{api_url}{OAUTH_TOKEN_PATH}",
        ),
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Make the OAuth2 client known before any config entry is loaded."""
    async_register_implementation(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UrbanJungle Care from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    )
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    api = UrbanJungleCareApi(
        async_get_clientsession(hass),
        OAuth2Auth(oauth_session),
        entry.data.get(CONF_API_URL, DEFAULT_API_URL),
    )

    coordinator = UrbanJungleCareCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Withdraw this Home Assistant from the account when the user removes the entry.

    This belongs here rather than in the unload: a reload or a restart unloads the entry
    too, and that must leave the integration record on the backend alone.
    """
    try:
        implementation = (
            await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
        )
        api = UrbanJungleCareApi(
            async_get_clientsession(hass),
            OAuth2Auth(config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)),
            entry.data.get(CONF_API_URL, DEFAULT_API_URL),
        )
        await api.delete_integration(entry.data[CONF_INTEGRATION_ID])
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Failed to delete integration from backend: %s", err)
