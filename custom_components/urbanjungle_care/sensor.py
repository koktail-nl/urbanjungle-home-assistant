"""Sensor platform for UrbanJungle Care."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import UrbanJungleCareCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UrbanJungle Care sensors from a config entry."""
    coordinator: UrbanJungleCareCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [UrbanJungleCareSyncStatusSensor(coordinator, entry)]

    for device in coordinator.data.get("devices", []):
        for sensor_type in SENSOR_TYPES:
            entities.append(
                UrbanJungleCareDeviceSensor(coordinator, device["id"], sensor_type)
            )

    async_add_entities(entities)
    _LOGGER.debug("Added %d sensor entities", len(entities))


class UrbanJungleCareSyncStatusSensor(CoordinatorEntity, SensorEntity):
    """Diagnostic sensor showing the sync frequency."""

    _attr_icon = "mdi:sync"
    _attr_name = "UrbanJungle Sync Status"

    def __init__(
        self, coordinator: UrbanJungleCareCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sync status sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_sync_status"

    @property
    def native_value(self) -> str:
        """Return the sync frequency."""
        return self.coordinator.sync_frequency

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return diagnostic attributes."""
        data = self.coordinator.data or {}
        return {
            "is_premium": self.coordinator.is_premium,
            "last_sync": data.get("last_sync"),
            "devices_synced": len(data.get("devices", [])),
            "plants_synced": len(data.get("plants", [])),
        }


class UrbanJungleCareDeviceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for a single device capability (temperature, moisture, ...)."""

    def __init__(
        self,
        coordinator: UrbanJungleCareCoordinator,
        device_id: str,
        sensor_type: str,
    ) -> None:
        """Initialize the device sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{device_id}_{sensor_type}"

        config = SENSOR_TYPES[sensor_type]
        self._attr_name = config["name"]
        self._attr_native_unit_of_measurement = config["unit"]
        self._attr_icon = config["icon"]
        self._attr_device_class = config.get("device_class")

    def _device(self) -> Optional[Dict[str, Any]]:
        """Return this entity's device record from coordinator data."""
        devices = (self.coordinator.data or {}).get("devices", [])
        return next((d for d in devices if d.get("id") == self._device_id), None)

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        """Group all capabilities under one HA device."""
        device = self._device()
        if not device:
            return None
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("name", "UrbanJungle Device"),
            manufacturer="UrbanJungle Care",
        )

    @property
    def native_value(self):
        """Return the latest value for this capability."""
        device = self._device()
        if not device:
            return None

        for sensor in device.get("capabilitySensors", []):
            if sensor.get("type") != self._sensor_type:
                continue
            history = sensor.get("history") or []
            if history:
                return history[-1].get("value")
            return None
        return None

    @property
    def available(self) -> bool:
        """Return whether the entity has data."""
        return (
            self.coordinator.last_update_success and self.native_value is not None
        )
