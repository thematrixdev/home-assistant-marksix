"""The Mark Six HK integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)
PLATFORMS: list[Platform] = [Platform.SENSOR]

GRAPHQL_URL = "https://info.cld.hkjc.com/graphql/base/"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Mark Six HK component."""
    return True

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the Mark Six HK sensor platform."""
    async_add_entities(
        [
            MarkSixHKSensor(hass, "last_draw", 0),
            MarkSixHKSensor(hass, "next_draw", 1),
        ],
        True,
    )

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mark Six HK from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

class MarkSixHKSensor(SensorEntity):
    """Representation of a Mark Six HK sensor."""

    def __init__(self, hass: HomeAssistant, name: str, index: int) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._name = name
        self._index = index
        self._attr_native_value = "OK"
        self._attr_extra_state_attributes = {}

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"Mark Six HK {self._name}"

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.post(GRAPHQL_URL) as response:
                        data = await response.json()
                        if "data" in data and "lotteryDraws" in data["data"]:
                            draws = data["data"]["lotteryDraws"]
                            if len(draws) > self._index:
                                self._attr_extra_state_attributes = draws[self._index]
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
