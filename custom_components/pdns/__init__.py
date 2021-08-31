"""Integrate with PowerDNS service."""
import asyncio
from datetime import timedelta
import logging

import aiohttp
from aiohttp import BasicAuth
import async_timeout
import voluptuous as vol

from homeassistant.const import (
    CONF_DOMAIN,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_SCAN_INTERVAL
)

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

DOMAIN = "powerdns"

DEFAULT_INTERVAL = timedelta(minutes=10)

TIMEOUT = 10
CONF_URL = "url"

PDNS_ERRORS = {
    "nohost": "Hostname supplied does not exist under specified account",
    "badauth": "Invalid username password combination",
    "badagent": "Client disabled",
    "!donator": "An update request was sent with a feature that is not available",
    "abuse": "Username is blocked due to abuse",
}

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_DOMAIN): cv.string,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Requied(CONF_URL): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL): vol.All(
                    cv.time_period, cv.positive_timedelta
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass, config):
    """Initialize the component."""
    conf = config[DOMAIN]
    domain = conf.get(CONF_DOMAIN)
    user = conf.get(CONF_USERNAME)
    password = conf.get(CONF_PASSWORD)
    interval = conf.get(CONF_SCAN_INTERVAL)
    url = conf.get(CONF_URL)

    session = async_get_clientsession(hass)

    result = await _update_pdns(hass, session, domain, user, password)

    if not result:
        return False

    async def update_domain_interval(now):
        """Update the entry."""
        await _update_pdns(hass, session, domain, user, password)

    async_track_time_interval(hass, update_domain_interval, interval)

    return True


async def _update_pdns(hass, session, domain, user, password):
    """Update."""
    params = {"myip": "1.2.3.4", "hostname": domain}
    authentication = BasicAuth(user, password)

    try:        
        with async_timeout.timeout(TIMEOUT):
            resp = await session.get(url, params=params, auth=authentication)
            body = await resp.text()

            if body.startswith("good") or body.startswith("nochg"):
                _LOGGER.info("Updating for domain: %s", domain)

                return True

            _LOGGER.warning("Updating failed: %s => %s", domain, PDNS_ERRORS[body.strip()])

    except aiohttp.ClientError:
        _LOGGER.warning("Can't connect to API")

    except asyncio.TimeoutError:
        _LOGGER.warning("Timeout from API for domain: %s", domain)

    return False
