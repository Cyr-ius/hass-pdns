"""PDNS Api."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from aiohttp import BasicAuth, ClientError, ClientSession

MYIP_CHECK = "https://v4.ident.me/"
PDNS_ERRORS = {
    "nohost": "Hostname supplied does not exist under specified account",
    "badauth": "Invalid username password combination",
    "badagent": "Client disabled",
    "!donator": "An update request was sent with a feature that is not available",
    "abuse": "Username is blocked due to abuse",
}

_LOGGER = logging.getLogger(__name__)


class PDNS:
    """Powerdns class."""

    def __init__(
        self, servername: str, alias: str, username: str, password: str, session=None
    ) -> None:
        """Initialize."""
        self.url = f"https://{servername}/nic/update"
        self.alias = alias
        self.session = session if session else ClientSession()
        self.authentification = BasicAuth(username, password)

    async def async_update(self) -> dict(str, str, datetime):
        """Update Alias to Power DNS."""
        try:
            public_ip = await self._async_get_public_ip()
            params = {"myip": public_ip, "hostname": self.alias}
            response = await self.session.get(self.url, params=params, auth=self.authentification)
            if response.status != 200:
                raise CannotConnect(f"Can't connect to API ({response.status})")
            body = await response.text()
            if body.startswith("good") or body.startswith("nochg"):
                state = body.strip()
                _LOGGER.debug("State: %s",state)
                return {
                    "state": state, "public_ip": public_ip, "last_seen": datetime.now()
                }
            raise CannotConnect(f"Can't connect to API ({body})")
        except ClientError as error:
            raise CannotConnect(error) from error
        except asyncio.TimeoutError as error:
            raise TimeoutExpired(f"API Timeout from {self.alias}") from error

    async def _async_get_public_ip(self) -> None:
        """Get Public ip address."""
        try:
            response = await self.session.get(MYIP_CHECK)
            if response.status != 200:
                raise CannotConnect(f"Can't fetch public ip ({response.status})")
            public_ip = await response.text()
            _LOGGER.debug("Public Ip: %s",public_ip)
            return public_ip
        except asyncio.TimeoutError as error:
            raise TimeoutExpired("Timeout to get public ip address") from error
        except Exception as error:
            raise DetectionFailed(str(error)) from error


class PDNSFailed(Exception):
    """Error to indicate there is invalid pdns communication."""


class DetectionFailed(PDNSFailed):
    """Error to indicate there is invalid retrieve public ip address."""


class CannotConnect(PDNSFailed):
    """Error to indicate we cannot connect."""


class TimeoutExpired(PDNSFailed):
    """Error to indicate there is invalid auth."""
