"""Refresh button entity."""

from homeassistant.components.button import DOMAIN as ENTITY_DOMAIN, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_SW_VERSION,
    DOMAIN,
)
from .sensor import EVNDevice


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Setup the button platform."""
    device: EVNDevice = hass.data[DOMAIN][entry.entry_id]["device"]
    async_add_entities([EVNRefreshButton(device)])


class EVNRefreshButton(ButtonEntity):
    """Button forcing an immediate data refresh."""

    _attr_icon = "mdi:refresh"

    def __init__(self, device: EVNDevice) -> None:
        self._device = device
        self._attr_name = f"{device._name} Làm mới dữ liệu"
        self._attr_unique_id = f"{device._customer_code}_refresh".lower()
        self.entity_id = f"{ENTITY_DOMAIN}.{device._customer_code}_refresh".lower()

    async def async_press(self) -> None:
        await self._device.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            name=self._device._name,
            identifiers={(DOMAIN, self._device._customer_code)},
            manufacturer=CONF_DEVICE_MANUFACTURER,
            sw_version=CONF_DEVICE_SW_VERSION,
            model=CONF_DEVICE_MODEL,
        )
