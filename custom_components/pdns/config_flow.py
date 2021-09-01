"""Config flow to configure PowerDNS Dynhost."""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_DOMAIN,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import (
    DOMAIN,
    CannotConnect,
    TimeoutExpired,
    PDNSFailed,
    DetectionFailed,
    async_update_pdns,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DOMAIN): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_URL): cv.string,
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
                await async_update_pdns(
                    self.hass,
                    session,
                    url=user_input[CONF_URL],
                    domain=user_input[CONF_DOMAIN],
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
                return self.async_create_entry(
                    title="PowerDNS Dynhost", data=user_input
                )
            except CannotConnect:
                errors["base"] = "login_incorrect"
            except TimeoutExpired:
                errors["base"] = "timeout"
            except PDNSFailed as err:
                errors["base"] = err.args[0]
            except DetectionFailed:
                errors["base"] = "detect_failed"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
