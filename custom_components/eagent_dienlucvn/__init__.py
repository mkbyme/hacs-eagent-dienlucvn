from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import eagent_dienlucvn
from .const import DOMAIN
from .sensor import EVNDevice

PLATFORMS = ["sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Establish connection with eAgent EVN."""
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {}).update(entry.data)
    hass.data[DOMAIN][entry.entry_id].update(entry.options)
    entry_config = hass.data[DOMAIN][entry.entry_id]
    device = EVNDevice(entry_config, eagent_dienlucvn.EAgentAPI(hass, True))
    await device.async_create_coordinator(hass)
    entry_config["device"] = device
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
