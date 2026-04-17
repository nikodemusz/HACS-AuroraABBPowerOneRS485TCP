"""Data update coordinator for Aurora ABB PowerOne TCP."""

from __future__ import annotations

from datetime import timedelta
import logging
from time import sleep
from typing import Any

from aurorapy.client import (
    AuroraError,
    AuroraSerialClient,
    AuroraTCPClient,
    AuroraTimeoutError,
)
from serial import SerialException

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, PROTOCOL_TCP

_LOGGER = logging.getLogger(__name__)

type AuroraAbbConfigEntry = ConfigEntry["AuroraAbbDataUpdateCoordinator"]


class AuroraAbbDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Aurora ABB PowerOne data."""

    config_entry: AuroraAbbConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: AuroraAbbConfigEntry,
        protocol: str,
        address: int,
        serial_port: str | None = None,
        host: str | None = None,
        tcp_port: int | None = None,
        timeout: float = 3.0,
        scan_interval_seconds: int = 30,
    ) -> None:
        self.available_prev = False
        self.available = False
        self.protocol = protocol
        self.address = address
        self.serial_port = serial_port
        self.host = host
        self.tcp_port = tcp_port
        self.timeout = timeout

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )

    def _build_client(self):
        """Create a fresh client instance."""
        if self.protocol == PROTOCOL_TCP:
            return AuroraTCPClient(
                ip=self.host,
                port=self.tcp_port,
                address=self.address,
                timeout=self.timeout,
            )

        return AuroraSerialClient(
            address=self.address,
            port=self.serial_port,
            parity="N",
            timeout=self.timeout,
        )

    def _close_client(self, client) -> None:
        """Close a client safely."""
        try:
            if self.protocol == PROTOCOL_TCP:
                if getattr(client, "s", None):
                    client.close()
            else:
                serline = getattr(client, "serline", None)
                if serline is not None and serline.isOpen():
                    client.close()
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Ignoring close error", exc_info=True)

    def _update_data(self) -> dict[str, Any]:
        """Fetch new state data for all sensors."""
        self.available_prev = self.available
        retries = 3
        last_error: Exception | None = None

        while retries > 0:
            client = self._build_client()
            try:
                client.connect()

                grid_voltage = client.measure(1, True)
                grid_current = client.measure(2, True)
                power_watts = client.measure(3, True)
                frequency = client.measure(4)
                i_leak_dcdc = client.measure(6)
                i_leak_inverter = client.measure(7)
                power_in_1 = client.measure(8)
                power_in_2 = client.measure(9)
                temperature_c = client.measure(21)
                voltage_in_1 = client.measure(23)
                current_in_1 = client.measure(25)
                voltage_in_2 = client.measure(26)
                current_in_2 = client.measure(27)
                r_iso = client.measure(30)
                energy_wh = client.cumulated_energy(5)
                alarm = client.alarms()[0]

                data: dict[str, Any] = {
                    "grid_voltage": round(grid_voltage, 1),
                    "grid_current": round(grid_current, 1),
                    "instantaneouspower": round(power_watts, 1),
                    "grid_frequency": round(frequency, 1),
                    "i_leak_dcdc": round(i_leak_dcdc, 3),
                    "i_leak_inverter": round(i_leak_inverter, 3),
                    "power_in_1": round(power_in_1, 1),
                    "power_in_2": round(power_in_2, 1),
                    "temp": round(temperature_c, 1),
                    "voltage_in_1": round(voltage_in_1, 1),
                    "current_in_1": round(current_in_1, 1),
                    "voltage_in_2": round(voltage_in_2, 1),
                    "current_in_2": round(current_in_2, 1),
                    "r_iso": round(r_iso, 3),
                    "totalenergy": round(energy_wh / 1000, 2),
                    "alarm": alarm,
                }

                self.available = True

                if self.available != self.available_prev:
                    _LOGGER.warning("Communication with %s back online", self.name)

                return data

            except (AuroraTimeoutError, SerialException, AuroraError) as error:
                last_error = error
                self.available = False
                retries -= 1

                if retries > 0:
                    _LOGGER.debug(
                        "Aurora communication error %r, %d retries remaining",
                        error,
                        retries,
                    )
                    sleep(1)

            finally:
                self._close_client(client)

        if self.available != self.available_prev:
            _LOGGER.warning("Communication with %s lost", self.name)

        raise UpdateFailed(f"No response from inverter: {last_error}") from last_error

    async def _async_update_data(self) -> dict[str, Any]:
        """Update inverter data in the executor."""
        return await self.hass.async_add_executor_job(self._update_data)

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator cleanly."""
        return
