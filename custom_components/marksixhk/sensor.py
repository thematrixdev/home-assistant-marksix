"""Support for Mark Six HK sensors."""
from __future__ import annotations

from datetime import timedelta
import logging
import aiohttp
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)

GRAPHQL_URL = "https://info.cld.hkjc.com/graphql/base/"
GRAPHQL_QUERY = """
fragment lotteryDrawsFragment on LotteryDraw {
  id
  year
  no
  openDate
  closeDate
  drawDate
  status
  snowballCode
  snowballName_en
  snowballName_ch
  lotteryPool {
    sell
    status
    totalInvestment
    jackpot
    unitBet
    estimatedPrize
    derivedFirstPrizeDiv
    lotteryPrizes {
      type
      winningUnit
      dividend
    }
  }
  drawResult {
    drawnNo
    xDrawnNo
  }
}

query marksixDraw {
  timeOffset {
    m6
    ts
  }
  lotteryDraws {
    ...lotteryDrawsFragment
  }
}
"""

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mark Six HK from a config entry."""
    async_add_entities(
        [
            MarkSixHKSensor(hass, "Last Draw", 0),
            MarkSixHKSensor(hass, "Next Draw", 1),
        ],
        True,
    )

class MarkSixHKSensor(SensorEntity):
    """Representation of a Mark Six HK sensor."""

    def __init__(self, hass: HomeAssistant, name: str, index: int) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._name = name
        self._index = index
        self._attr_native_value = None
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
                    async with session.post(
                        GRAPHQL_URL,
                        json={
                            "operationName": "marksixDraw",
                            "variables": {},
                            "query": GRAPHQL_QUERY,
                        },
                    ) as response:
                        data = await response.json()
                        if "data" in data and "lotteryDraws" in data["data"]:
                            draws = data["data"]["lotteryDraws"]
                            if len(draws) > self._index:
                                draw = draws[self._index]
                                self._attr_native_value = draw.get("drawDate")[0:10]
                                self._attr_extra_state_attributes = draw
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
