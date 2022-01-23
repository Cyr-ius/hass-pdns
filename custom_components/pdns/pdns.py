"""PDNS Api."""
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

    def __init__(self, servername, alias, username, password, session=None):
        """Initialize."""
        self.ip = None
        self.url = f"https://{servername}/nic/update"
        self.alias = alias
        self.session = session if session else ClientSession()
        self.authentification = BasicAuth(username, password)

    async def async_update(self):
        """Update Alias to Power DNS."""
        self.ip = await self._async_get_public_ip()
        try:
            params = {"myip": self.ip, "hostname": self.alias}
            resp = await self.session.get(
                self.url, params=params, auth=self.authentification
            )
            body = await resp.text()
            if body.startswith("good") or body.startswith("nochg"):
                return {
                    "state": body.strip(),
                    "public_ip": self.ip,
                    "last_seen": datetime.now(),
                }
            raise PDNSFailed(body.strip(), self.alias)
        except ClientError as error:
            raise CannotConnect("Can't connect to API : %s", error) from error
        except asyncio.TimeoutError as error:
            raise TimeoutExpired(f"API Timeout from {self.alias}") from error

    async def _async_get_public_ip(self):
        """Get Public ip address."""
        try:
            resp = await self.session.get(MYIP_CHECK)
            return await resp.text()
        except asyncio.TimeoutError as error:
            raise TimeoutExpired("Timeout to get public ip address") from error
        except Exception as error:
            raise DetectionFailed("Get public ip address failed %s", error) from error


class PDNSFailed(Exception):
    """Error to indicate there is invalid pdns communication."""

    def __init__(self, state, domain):
        """Init."""
        self.state = state
        self.domain = domain
        self.message = "Failed: %s => %s" % (PDNS_ERRORS[state], domain)


class DetectionFailed(Exception):
    """Error to indicate there is invalid retrieve public ip address."""


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class TimeoutExpired(Exception):
    """Error to indicate there is invalid auth."""
