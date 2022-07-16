"""binary sensor entities."""
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer binary sensor setup to the shared sensor module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([DyndnsStatus(coordinator)])


class DyndnsStatus(CoordinatorEntity, BinarySensorEntity):
    """Representation of a status sensor."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = "Dynamic Update"
    _attr_unique_id = "dynamic_update"

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_extra_state_attributes = coordinator.data

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.coordinator.data.get("public_ip") is None
