"""binary sensor entities."""
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Defer binary sensor setup to the shared sensor module."""
    coordinator = hass.data[DOMAIN]
    async_add_entities([DyndnsStatus(coordinator)])


class DyndnsStatus(CoordinatorEntity, BinarySensorEntity):
    """Representation of a VocalMsg sensor."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = "Dynamic Update"
    _attr_unique_id = "dynamic_update"

    def __init__(self, coordinator):
        """Initialize the sensor."""
        self.coordinator = coordinator

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.coordinator.data.get("public_ip") is None

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        return self.coordinator.data
