"""Data update coordinator for UrbanJungle Care.

Two directions per cycle:
- pull the account's devices/plants (cloud -> Home Assistant entities);
- read Home Assistant's own ``xiaomi_ble`` plant-sensor entities and push their
  values up to UrbanJungle (HA -> API), auto-registering unknown sensors.

Letting ``xiaomi_ble`` parse the sensors means the full (and possibly
encrypted) Xiaomi/Mi Flora advertisements are decoded correctly, instead of
re-implementing the wire format here.

Sync frequency follows the subscription: every 15 minutes for premium/testers,
daily otherwise.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, OAuth2TokenError, UrbanJungleCareApi
from .const import (
    CAP_BATTERY,
    CAP_LUMINANCE,
    CAP_MOISTURE,
    CAP_NUTRITION,
    CAP_TEMPERATURE,
    CONF_INTEGRATION_ID,
    DOMAIN,
    SYNC_INTERVAL_FREE_HOURS,
    SYNC_INTERVAL_PREMIUM_MINUTES,
)

_LOGGER = logging.getLogger(__name__)

# Source platform of the plant sensors we read from.
_XIAOMI_PLATFORM = "xiaomi_ble"

# xiaomi_ble unique_id key suffix -> UrbanJungle capability type.
_XIAOMI_KEY_MAP = {
    "temperature": CAP_TEMPERATURE,
    "moisture": CAP_MOISTURE,
    "illuminance": CAP_LUMINANCE,
    "conductivity": CAP_NUTRITION,
    "battery": CAP_BATTERY,
}

_UNAVAILABLE_STATES = ("unknown", "unavailable")


def _normalize_address(address: Optional[str]) -> str:
    """Normalize a BLE MAC address for comparison (strip separators, lowercase)."""
    if not address:
        return ""
    return address.replace(":", "").replace("-", "").lower()


class UrbanJungleCareCoordinator(DataUpdateCoordinator):
    """Coordinate data updates from the UrbanJungle API and xiaomi_ble sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: UrbanJungleCareApi,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.entry = entry
        self.integration_id = entry.data[CONF_INTEGRATION_ID]
        self._is_premium = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SYNC_INTERVAL_PREMIUM_MINUTES),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the API and push xiaomi_ble readings upstream."""
        try:
            subscription = await self.api.get_subscription()
            profile = await self.api.get_profile() or {}
            self._apply_sync_interval(subscription, profile)

            devices = await self.api.get_devices()
            await self._push_from_xiaomi_ble(devices)

            plants = await self.api.get_plants()

            return {
                "devices": devices,
                "plants": plants,
                "profile": profile,
                "is_premium": self._is_premium,
                "last_sync": datetime.now(timezone.utc).isoformat(),
            }
        except OAuth2TokenError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _apply_sync_interval(
        self, subscription: Optional[Dict[str, Any]], profile: Dict[str, Any]
    ) -> None:
        """Set the update interval from subscription/tester status (Homey parity)."""
        is_tester = profile.get("tester") is True
        self._is_premium = subscription is not None or is_tester

        if self._is_premium:
            interval = timedelta(minutes=SYNC_INTERVAL_PREMIUM_MINUTES)
        else:
            interval = timedelta(hours=SYNC_INTERVAL_FREE_HOURS)

        if self.update_interval != interval:
            _LOGGER.debug("Sync interval -> %s", interval)
            self.update_interval = interval

    async def _push_from_xiaomi_ble(self, devices: List[Dict[str, Any]]) -> None:
        """Read xiaomi_ble plant sensors and push their values to UrbanJungle."""
        dev_reg = dr.async_get(self.hass)
        ent_reg = er.async_get(self.hass)

        for device in list(dev_reg.devices.values()):
            address = next(
                (v for (kind, v) in device.connections if kind == CONNECTION_BLUETOOTH),
                None,
            )
            if not address:
                continue

            values = self._read_xiaomi_values(ent_reg, device.id)
            # Only plant sensors (Mi Flora) expose moisture + conductivity.
            if CAP_NUTRITION not in values and CAP_MOISTURE not in values:
                continue

            try:
                await self._push_or_register(
                    address, device.name or f"Sensor {address}", values, devices
                )
            except ApiError as err:
                _LOGGER.error("Failed to push metrics for %s: %s", address, err)

    def _read_xiaomi_values(
        self, ent_reg: er.EntityRegistry, device_id: str
    ) -> Dict[str, float]:
        """Read the current capability values from a device's xiaomi_ble sensors."""
        values: Dict[str, float] = {}
        for entry in er.async_entries_for_device(ent_reg, device_id):
            if entry.platform != _XIAOMI_PLATFORM or entry.domain != "sensor":
                continue
            capability = _XIAOMI_KEY_MAP.get(entry.unique_id.rsplit("-", 1)[-1])
            if not capability:
                continue
            state = self.hass.states.get(entry.entity_id)
            if state is None or state.state in _UNAVAILABLE_STATES:
                continue
            try:
                values[capability] = float(state.state)
            except (ValueError, TypeError):
                continue
        return values

    async def _push_or_register(
        self,
        address: str,
        name: str,
        values: Dict[str, float],
        devices: List[Dict[str, Any]],
    ) -> None:
        """Push metrics for ``address``, registering the device if unknown."""
        if not values:
            return

        target = _normalize_address(address)
        device = next(
            (d for d in devices if _normalize_address(d.get("bleAddress")) == target),
            None,
        )

        if device is None:
            device = {
                "id": str(uuid.uuid4()),
                "bleAddress": address,
                "name": name,
                "plant": None,
                "lastUpdatedAt": datetime.now(timezone.utc).isoformat(),
                "capabilitySensors": [],
                "identificationType": None,
                "deviceUuid": None,
            }
            await self.api.add_device_entity(device)
            devices.append(device)
            _LOGGER.info("Registered device %s from xiaomi_ble", address)

        timestamp = datetime.now(timezone.utc).isoformat()
        metrics = [
            {
                "bleAddress": device.get("bleAddress"),
                "deviceId": device.get("id"),
                "plantId": device.get("plant"),
                "type": metric_type,
                "value": value,
                "lastUpdated": timestamp,
            }
            for metric_type, value in values.items()
        ]
        await self.api.add_device_metrics(device["id"], metrics)
        _LOGGER.debug("Pushed %d metric(s) for %s", len(metrics), address)

    @property
    def is_premium(self) -> bool:
        """Return whether the user is premium (or a tester)."""
        return self._is_premium

    @property
    def sync_frequency(self) -> str:
        """Human-readable sync frequency."""
        if self._is_premium:
            return f"Every {SYNC_INTERVAL_PREMIUM_MINUTES} minutes"
        return f"Every {SYNC_INTERVAL_FREE_HOURS} hours"
