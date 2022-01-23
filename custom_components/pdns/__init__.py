"""Integrate with PowerDNS service."""
import logging
from datetime import timedelta

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .pdns import PDNS, CannotConnect, TimeoutExpired, PDNSFailed, DetectionFailed

DEFAULT_INTERVAL = 15
DOMAIN = "pdns"
CONF_PDNSSRV = "pdns_server"
CONF_ALIAS = "dns_alias"
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Load configuration for component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, config_entry):
    """Initialize the component."""
    alias = config_entry.data.get(CONF_ALIAS)
    username = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    servername = config_entry.data.get(CONF_PDNSSRV)

    session = async_create_clientsession(hass)
    client = PDNS(servername, alias, username, password, session)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=client.async_update,
        update_interval=timedelta(minutes=DEFAULT_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = coordinator
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")
    return True
