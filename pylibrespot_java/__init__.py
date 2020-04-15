"""This library wraps the librespot-java API for use with Home Assistant."""
__version__ = "0.1.0"
import asyncio
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)


def _debug_string(string_base, status) -> str:
    """Helper for logger debug strings."""
    if status == 204:
        return string_base + " No active session"
    if status == 500:
        return string_base + " Invalid session"
    if status == 503:
        return string_base + " Session is reconnecting"
    return ""


class LibrespotJavaAPI:
    """Class for interfacing with librespot-java API."""

    def __init__(self, websession, ip_address, api_port):
        self._ip_address = ip_address
        self._api_port = api_port
        self._websession = websession

    async def post_request(self, endpoint, data=None) -> int:
        """Helper function to put to endpoint."""
        url = f"http://{self._ip_address}:{self._api_port}/{endpoint}"
        _LOGGER.debug("POST request to %s with payload %s.", url, data)
        response = await self._websession.post(url=url, data=data)
        return response

    async def start_websocket_handler(
        self, update_callback, websocket_reconnect_time,
    ) -> None:
        """Websocket handler daemon."""
        _LOGGER.debug("Starting websocket handler")
        url = f"http://{self._ip_address}:{self._api_port}/events"
        while True:
            try:
                async with self._websession.ws_connect(url) as ws:
                    async for msg in ws:
                        json = msg.json()
                        _LOGGER.debug("Message received: %s", json)
                        await update_callback(json)
                _LOGGER.debug(
                    "WebSocket disconnected, will retry in %s seconds.",
                    websocket_reconnect_time,
                )
                await asyncio.sleep(websocket_reconnect_time)
            except (asyncio.TimeoutError, aiohttp.ClientError):
                _LOGGER.error(
                    "Can not connect to WebSocket at %s, will retry in %s seconds.",
                    url,
                    websocket_reconnect_time,
                )
                await asyncio.sleep(websocket_reconnect_time)
                continue

    async def player_load(self, uri, play) -> int:
        """Load track from URI."""
        resp = await self.post_request(
            endpoint="player/load", data={"uri": uri, "play": play}
        )
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(_debug_string("Unable to load track.", resp.status))
        return resp.status

    async def player_pause(self) -> int:
        """Pause playback."""
        resp = await self.post_request(endpoint="player/pause")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(_debug_string("Unable to pause player.", resp.status))
        return resp.status

    async def player_resume(self) -> int:
        """Resume playback."""
        resp = await self.post_request(endpoint="player/resume")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(_debug_string("Unable to resume player.", resp.status))
        return resp.status

    async def player_next(self) -> int:
        """Skip to next track."""
        resp = await self.post_request(endpoint="player/next")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(
                _debug_string("Unable to skip to the next track.", resp.status)
            )
        return resp.status

    async def player_prev(self) -> int:
        """Skip to previous track."""
        resp = await self.post_request(endpoint="player/prev")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(
                _debug_string("Unable to skip to the previous track.", resp.status)
            )
        return resp.status

    async def player_set_volume(self, volume: int) -> int:
        """Set volume to a given volume between 0 and 65536."""
        resp = await self.post_request(
            endpoint="player/set-volume", data={"volume": volume}
        )
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(_debug_string("Unable to set the volume.", resp.status))
        return resp.status

    async def player_volume_up(self) -> int:
        """Turn up the volume a little bit."""
        resp = await self.post_request(endpoint="player/volume-up")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(_debug_string("Unable to turn the volume up.", resp.status))
        return resp.status

    async def player_volume_down(self) -> int:
        """Turn down the volume a little bit."""
        resp = await self.post_request(endpoint="player/volume-down")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(_debug_string("Unable to turn the volume down.", resp.status))
        return resp.status

    async def player_current(self) -> dict:
        """Retrieve information about the current track."""
        resp = await self.post_request(endpoint="player/current")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(
                _debug_string(
                    "Unable to retrieve information about the current track.",
                    resp.status,
                )
            )
        json = await resp.json(content_type=None)
        return json

    async def metadata(self, uri: str) -> dict:
        """Retrieve metadata."""
        resp = await self.post_request(endpoint=f"metadata/{uri}")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(
                _debug_string(f"Unable to get metadata for {uri}.", resp.status)
            )
        json = await resp.json(content_type=None)
        return json

    async def search(self, query: str) -> dict:
        """Make a search."""
        resp = await self.post_request(endpoint=f"search/{query}")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(_debug_string(f"Unable to search for {query}.", resp.status))
        json = await resp.json(content_type=None)
        return json

    async def token(self, scope: str) -> dict:
        """Request an access token for a specific scope."""
        resp = await self.post_request(endpoint=f"token/{scope}")
        if resp.status in [204, 500, 503]:
            _LOGGER.debug(
                _debug_string(f"Unable to get token for {scope}.", resp.status)
            )
        json = await resp.json(content_type=None)
        return json


class LibrespotJavaData:
    """Represent a librespot-java server."""

    def __init__(self):
        """Initialize the LibrespotJava class."""
        self._player_status = None
        self._volume = None
        self._track_info = None

    @property
    def name(self):
        """Name getter."""
        return "librespot-java"

    @property
    def player_status(self):
        """Player status getter."""
        return self._player_status

    @player_status.setter
    def player_status(self, value):
        """Player status setter."""
        self._player_status = value

    @property
    def volume(self):
        """Volume getter."""
        return self._volume

    @volume.setter
    def volume(self, value):
        """Volume setter."""
        self._volume = value

    @property
    def track_info(self):
        """Track info getter."""
        return self._track_info

    @track_info.setter
    def track_info(self, value):
        """Track info setter."""
        self._track_info = value
