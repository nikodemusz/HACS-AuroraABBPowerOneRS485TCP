"""Data update coordinator for Aurora ABB PowerOne TCP."""

from __future__ import annotations

from datetime import timedelta
import logging
from time import sleep
from typing import Any

from aurorapy.client import AuroraError, AuroraSerialClient, AuroraTCPClient, AuroraTimeoutError
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
        timeout: float = 1.0,
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
        self.client = self._build_client()
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )

    def _build_client(self):
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

    def _close_client(self) -> None:
        try:
            if self.protocol == PROTOCOL_TCP:
                if getattr(self.client, "s", None):
                    self.client.close()
            else:
                serline = getattr(self.client, "serline", None)
                if serline is not None and serline.isOpen():
                    self.client.close()
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Ignoring close error", exc_info=True)

    def _update_data(self) -> dict[str, Any]:
        """Fetch new state data for all sensors."""
        data: dict[str, Any] = {}
        self.available_prev = self.available
        retries = 3

        while retries > 0:
            try:
                self.client.connect()
                grid_voltage = self.client.measure(1, True)
                grid_current = self.client.measure(2, True)
                power_watts = self.client.measure(3, True)
                frequency = self.client.measure(4)
                i_leak_dcdc = self.client.measure(6)
                i_leak_inverter = self.client.measure(7)
                power_in_1 = self.client.measure(8)
                power_in_2 = self.client.measure(9)
                temperature_c = self.client.measure(21)
                voltage_in_1 = self.client.measure(23)
                current_in_1 = self.client.measure(25)
                voltage_in_2 = self.client.measure(26)
                current_in_2 = self.client.measure(27)
                r_iso = self.client.measure(30)
                energy_wh = self.client.cumulated_energy(5)
                alarm = self.client.alarms()[0]
            except AuroraTimeoutError:
                self.available = False
                retries = 0
                _LOGGER.debug("No response from inverter")
            except (SerialException, AuroraError) as error:
                self.available = False
                retries -= 1
                if retries <= 0:
                    raise UpdateFailed(error) from error
                _LOGGER.debug("Aurora exception %r, %d retries remaining", error, retries)
                sleep(1)
            else:
                data["grid_voltage"] = round(grid_voltage, 1)
                data["grid_current"] = round(grid_current, 1)
                data["instantaneouspower"] = round(power_watts, 1)
                data["grid_frequency"] = round(frequency, 1)
                data["i_leak_dcdc"] = round(i_leak_dcdc, 3)
                data["i_leak_inverter"] = round(i_leak_inverter, 3)
                data["power_in_1"] = round(power_in_1, 1)
                data["power_in_2"] = round(power_in_2, 1)
                data["temp"] = round(temperature_c, 1)
                data["voltage_in_1"] = round(voltage_in_1, 1)
                data["current_in_1"] = round(current_in_1, 1)
                data["voltage_in_2"] = round(voltage_in_2, 1)
                data["current_in_2"] = round(current_in_2, 1)
                data["r_iso"] = round(r_iso, 3)
                data["totalenergy"] = round(energy_wh / 1000, 2)
                data["alarm"] = alarm
                self.available = True
                retries = 0
            finally:
                self._close_client()

        if self.available != self.available_prev:
            if self.available:
                _LOGGER.warning("Communication with %s back online", self.name)
            else:
                _LOGGER.warning("Communication with %s lost", self.name)

        return data

    async def _async_update_data(self) -> dict[str, Any]:
        """Update inverter data in the executor."""
        return await self.hass.async_add_executor_job(self._update_data)

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator cleanly."""
        await self.hass.async_add_executor_job(self._close_client)
