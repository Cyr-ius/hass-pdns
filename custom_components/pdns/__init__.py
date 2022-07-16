"""Integrate with PowerDNS service."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .pdns import PDNS, PDNSFailed

SCAN_INTERVAL = 15
DOMAIN = "pdns"
CONF_PDNSSRV = "pdns_server"
CONF_ALIAS = "dns_alias"
PLATFORMS = ["binary_sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialize the component."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = PDNSDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    if coordinator.data is None:
        return False

    hass.data[DOMAIN][entry.entry_id] = coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class PDNSDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to fetch datas."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Class to manage fetching data API."""
        session = async_create_clientsession(hass)
        self.pdns_client = PDNS(
            entry.data.get(CONF_PDNSSRV),
            entry.data.get(CONF_ALIAS),
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
            session,
        )
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=SCAN_INTERVAL)
        )

    async def _async_update_data(self) -> dict:
        try:
            return await self.pdns_client.async_update()
        except PDNSFailed as error:
            raise UpdateFailed(error) from error
