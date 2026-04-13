"""Aurora ABB PowerOne TCP integration."""

from __future__ import annotations

import importlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_HOST,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_TCP_PORT,
    CONF_TIMEOUT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import AuroraAbbDataUpdateCoordinator

type AuroraAbbConfigEntry = ConfigEntry[AuroraAbbDataUpdateCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AuroraAbbConfigEntry) -> bool:
    """Set up Aurora ABB PowerOne from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    options = entry.options
    coordinator = AuroraAbbDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
        protocol=entry.data[CONF_PROTOCOL],
        address=int(options.get(CONF_ADDRESS, entry.data[CONF_ADDRESS])),
        serial_port=options.get(CONF_PORT, entry.data.get(CONF_PORT)),
        host=options.get(CONF_HOST, entry.data.get(CONF_HOST)),
        tcp_port=int(options.get(CONF_TCP_PORT, entry.data.get(CONF_TCP_PORT, 0) or 0)),
        timeout=float(options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, 3.0))),
        scan_interval_seconds=int(options.get(CONF_SCAN_INTERVAL, 30)),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Pre-import platform modules in executor to avoid blocking import detection
    # on newer Home Assistant / Python versions.
    for platform in PLATFORMS:
        await hass.async_add_executor_job(
            importlib.import_module,
            f"{__package__}.{platform}",
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AuroraAbbConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        if entry.runtime_data:
            await entry.runtime_data.async_shutdown()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
"""The Aurora ABB PowerOne TCP integration."""

from __future__ import annotations

import importlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS

type AuroraConfigEntry = ConfigEntry

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from yaml (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AuroraConfigEntry) -> bool:
    """Set up Aurora ABB PowerOne from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Pre-import platform modules in the executor to avoid blocking imports
    # being detected in the event loop on newer HA/Python versions.
    for platform in PLATFORMS:
        await hass.async_add_executor_job(
            importlib.import_module,
            f"{__package__}.{platform}",
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AuroraConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
