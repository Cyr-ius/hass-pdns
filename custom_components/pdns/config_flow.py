"""Config flow to configure PowerDNS Dynhost."""

import asyncio
import logging


import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_DOMAIN,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import DOMAIN, _update_pdns

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DOMAIN): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_URL): cv.string,
        vol.Optional(CONF_IP_ADDRESS): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


class PDNSFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                _update_pdns(
                    self.hass,
                    session,
                    url=user_input[CONF_URL],
                    domain=user_input[CONF_USERNAME],
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_USERNAME],
                    ip=user_input.get(CONF_IP_ADDRESS),
                )
            except aiohttp.ClientError:
                errors["base"] = "login_inccorect"
            except asyncio.TimeoutError:
                errors["base"] = "timeout"

            if "base" not in errors:
                return self.async_create_entry(title="PowerDNS Dynhost", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
