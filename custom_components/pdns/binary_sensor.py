"""binary sensor entities."""
import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Defer binary sensor setup to the shared sensor module."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([DyndnsStatus(coordinator)])


class DyndnsStatus(BinarySensorEntity):
    """Representation of a VocalMsg sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        self.coordinator = coordinator

    @property
    def name(self):
        """Return name sensor."""
        return "Dynamic Update"

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        if self.coordinator.data.get("public_ip"):
            return True
        return False

    @property
    def unique_id(self):
        """Return unique_id."""
        return "dynamic_update"

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        return self.coordinator.data

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        self.coordinator.async_remove_listener(self.async_write_ha_state)

    async def async_update(self) -> None:
        """Update entity."""
        await self.coordinator.async_request_refresh()
