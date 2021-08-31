"""Integrate with PowerDNS service."""
import asyncio
import logging
from datetime import timedelta

import aiohttp
import async_timeout
from aiohttp import BasicAuth
from homeassistant.const import (
    CONF_DOMAIN,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

DEFAULT_INTERVAL = timedelta(minutes=15)
DOMAIN = "pdns"
TIMEOUT = 10
PDNS_ERRORS = {
    "nohost": "Hostname supplied does not exist under specified account",
    "badauth": "Invalid username password combination",
    "badagent": "Client disabled",
    "!donator": "An update request was sent with a feature that is not available",
    "abuse": "Username is blocked due to abuse",
}
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Load configuration for component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, config_entry):
    """Initialize the component."""
    domain = config_entry.data.get(CONF_DOMAIN)
    user = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    url = config_entry.data.get(CONF_URL)
    ip = config_entry.data.get(CONF_IP_ADDRESS)
    session = async_get_clientsession(hass)

    async def async_update_data():
        """Update the entry."""
        if await async_update_pdns(hass, session, url, domain, user, password, ip):
            return hass.data[DOMAIN]["status"]

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=DEFAULT_INTERVAL,
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise PlatformNotReady

    if coordinator.data is None:
        return False

    hass.data[DOMAIN]["coordinator"] = coordinator
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    return True


async def async_update_pdns(hass, session, url, domain, username, password, ip=None):
    """Update."""
    if ip is None:
        resp = await session.get("https://api.ipify.org")
        ip = await resp.text()

    params = {"myip": ip, "hostname": domain}
    authentification = BasicAuth(username, password)
    try:
        with async_timeout.timeout(TIMEOUT):
            resp = await session.get(url, params=params, auth=authentification)
            body = await resp.text()

            if body.startswith("good") or body.startswith("nochg"):
                _LOGGER.info("Updating for domain: %s", domain)
                hass.data[DOMAIN]["status"] = {"state": body.strip(), "public_ip": ip}
                return True
            _LOGGER.warning(
                "Updating failed: %s => %s", domain, PDNS_ERRORS[body.strip()]
            )
            hass.data[DOMAIN]["status"] = {
                "state": "update_failed",
                "public_ip": ip,
                "msg": PDNS_ERRORS[body.strip()],
            }
    except aiohttp.ClientError as err:
        _LOGGER.warning("Can't connect to API %s" % err)
        hass.data[DOMAIN]["status"] = {"state": "login_incorrect"}
    except asyncio.TimeoutError:
        _LOGGER.warning("Timeout from API for domain: %s", domain)
        hass.data[DOMAIN]["status"] = {"state": "timout"}

    return False


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")
    return True
