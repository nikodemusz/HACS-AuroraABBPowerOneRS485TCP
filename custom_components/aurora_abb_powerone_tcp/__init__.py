"""The Aurora ABB PowerOne TCP integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_TCP_PORT,
    CONF_TIMEOUT,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import AuroraAbbDataUpdateCoordinator


type AuroraConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from yaml (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AuroraConfigEntry) -> bool:
    """Set up Aurora ABB PowerOne from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    coordinator = AuroraAbbDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
        protocol=entry.data["protocol"],
        address=int(entry.options.get("address", entry.data["address"])),
        serial_port=entry.options.get("port", entry.data.get("port")),
        host=entry.options.get(CONF_HOST, entry.data.get(CONF_HOST)),
        tcp_port=int(entry.options.get(CONF_TCP_PORT, entry.data.get(CONF_TCP_PORT, 0))) or None,
        timeout=float(entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))),
        scan_interval_seconds=int(
            entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)
        ),
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AuroraConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: AuroraConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
