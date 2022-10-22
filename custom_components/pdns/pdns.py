"""PDNS Api."""
from __future__ import annotations

import asyncio
from datetime import datetime

from aiohttp import BasicAuth, ClientError, ClientSession

MYIP_CHECK = "https://api.ipify.org"
PDNS_ERRORS = {
    "nohost": "Hostname supplied does not exist under specified account",
    "badauth": "Invalid username password combination",
    "badagent": "Client disabled",
    "!donator": "An update request was sent with a feature that is not available",
    "abuse": "Username is blocked due to abuse",
}


class PDNS:
    """Powerdns class."""

    def __init__(
        self, servername: str, alias: str, username: str, password: str, session=None
    ) -> None:
        """Initialize."""
        self.ip = None
        self.url = f"https://{servername}/nic/update"
        self.alias = alias
        self.session = session if session else ClientSession()
        self.authentification = BasicAuth(username, password)

    async def async_update(self) -> dict(str, str, datetime):
        """Update Alias to Power DNS."""
        await self._async_get_public_ip()
        try:
            params = {"myip": self.ip, "hostname": self.alias}
            async with self.session as session:
                async with session.get(
                    self.url, params=params, auth=self.authentification
                ) as response:
                    if response.status == 200:
                        body = await response.text()
                        if body.startswith("good") or body.startswith("nochg"):
                            return {
                                "state": body.strip(),
                                "public_ip": self.ip,
                                "last_seen": datetime.now(),
                            }
                        raise CannotConnect(f"Can't connect to API ({body})")
                    raise CannotConnect(f"Can't connect to API ({response.status})")
        except ClientError as error:
            raise CannotConnect(f"Error {error.strerror}") from error
        except asyncio.TimeoutError as error:
            raise TimeoutExpired(f"API Timeout from {self.alias}") from error

    async def _async_get_public_ip(self) -> None:
        """Get Public ip address."""
        try:
            async with self.session as session:
                async with session.get(MYIP_CHECK) as response:
                    if response.status == 200:
                        self.ip = await response.text()
                    else:
                        raise CannotConnect(f"Can't fetch public ip ({response.status})")
        except asyncio.TimeoutError as error:
            raise TimeoutExpired("Timeout to get public ip address") from error
        except Exception as error:
            raise DetectionFailed("Get public ip address failed") from error


class PDNSFailed(Exception):
    """Error to indicate there is invalid pdns communication."""


class DetectionFailed(PDNSFailed):
    """Error to indicate there is invalid retrieve public ip address."""


class CannotConnect(PDNSFailed):
    """Error to indicate we cannot connect."""


class TimeoutExpired(PDNSFailed):
    """Error to indicate there is invalid auth."""
