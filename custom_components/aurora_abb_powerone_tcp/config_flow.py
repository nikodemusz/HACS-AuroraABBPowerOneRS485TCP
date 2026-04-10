"""Config flow for Aurora ABB PowerOne TCP integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from aurorapy.client import AuroraError, AuroraSerialClient, AuroraTCPClient
import voluptuous as vol

from homeassistant.components import usb
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import ATTR_SERIAL_NUMBER, CONF_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig, SelectSelector, SelectSelectorConfig

from .const import (
    ATTR_FIRMWARE,
    ATTR_MODEL,
    CONF_HOST,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_TCP_PORT,
    CONF_TIMEOUT,
    DEFAULT_ADDRESS,
    DEFAULT_INTEGRATION_TITLE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_TCP_PORT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_ADDRESS,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_ADDRESS,
    MIN_SCAN_INTERVAL_SECONDS,
    PROTOCOL_SERIAL,
    PROTOCOL_TCP,
)

_LOGGER = logging.getLogger(__name__)


async def async_scan_comports(hass: HomeAssistant) -> tuple[list[str] | None, str | None]:
    """Find available serial ports."""
    com_ports = await usb.async_scan_serial_ports(hass)
    com_ports_list = [port.device for port in com_ports]
    if com_ports_list:
        return com_ports_list, com_ports_list[0]
    return None, None


def validate_and_connect(_: HomeAssistant, data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the user input and fetch basic device info."""
    protocol = data[CONF_PROTOCOL]
    address = data[CONF_ADDRESS]
    timeout = float(data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))

    client = None
    ret: dict[str, Any] = {"title": DEFAULT_INTEGRATION_TITLE}
    try:
        if protocol == PROTOCOL_TCP:
            host = data[CONF_HOST]
            port = data[CONF_TCP_PORT]
            _LOGGER.debug("Initializing TCP client host=%s port=%s address=%s", host, port, address)
            client = AuroraTCPClient(ip=host, port=port, address=address, timeout=timeout)
        else:
            comport = data[CONF_PORT]
            _LOGGER.debug("Initializing serial client port=%s address=%s", comport, address)
            client = AuroraSerialClient(address=address, port=comport, parity="N", timeout=timeout)

        client.connect()
        ret[ATTR_SERIAL_NUMBER] = client.serial_number()
        ret[ATTR_MODEL] = f"{client.version()} ({client.pn()})"
        ret[ATTR_FIRMWARE] = client.firmware(1)
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001
                pass

    return ret


class AuroraABBConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aurora ABB PowerOne TCP."""

    VERSION = 1

    def __init__(self) -> None:
        self._com_ports_list: list[str] | None = None
        self._default_com_port: str | None = None

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return AuroraABBOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose transport protocol."""
        if user_input is not None:
            if user_input[CONF_PROTOCOL] == PROTOCOL_TCP:
                return await self.async_step_tcp()
            return await self.async_step_serial()

        selector = SelectSelector(
            SelectSelectorConfig(options=[PROTOCOL_TCP, PROTOCOL_SERIAL], translation_key="protocol")
        )
        schema = vol.Schema({vol.Required(CONF_PROTOCOL, default=PROTOCOL_TCP): selector})
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_serial(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Configure serial access."""
        errors: dict[str, str] = {}

        if self._com_ports_list is None:
            self._com_ports_list, self._default_com_port = await async_scan_comports(self.hass)

        if user_input is not None:
            user_input[CONF_PROTOCOL] = PROTOCOL_SERIAL
            try:
                info = await self.hass.async_add_executor_job(validate_and_connect, self.hass, user_input)
            except OSError as error:
                if getattr(error, "errno", None) == 19:
                    errors["base"] = "invalid_serial_port"
                else:
                    errors["base"] = "cannot_connect"
            except AuroraError as error:
                msg = str(error)
                if "could not open port" in msg.lower():
                    errors["base"] = "cannot_open_serial_port"
                elif "no response after" in msg.lower() or "timeout" in msg.lower():
                    errors["base"] = "cannot_connect"
                else:
                    _LOGGER.exception("Unexpected Aurora serial error during setup")
                    errors["base"] = "cannot_connect"
            else:
                info.update(user_input)
                await self.async_set_unique_id(info[ATTR_SERIAL_NUMBER])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info[ATTR_SERIAL_NUMBER], data=info)

        if not self._default_com_port:
            errors["base"] = errors.get("base", "no_serial_ports")
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_PORT, default="/dev/ttyUSB0"): str,
                    vol.Required(CONF_ADDRESS, default=DEFAULT_ADDRESS): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_ADDRESS, max=MAX_ADDRESS)
                    ),
                    vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): NumberSelector(
                        NumberSelectorConfig(min=0.5, max=10, step=0.5)
                    ),
                }
            )
        else:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_PORT, default=self._default_com_port): vol.In(self._com_ports_list),
                    vol.Required(CONF_ADDRESS, default=DEFAULT_ADDRESS): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_ADDRESS, max=MAX_ADDRESS)
                    ),
                    vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): NumberSelector(
                        NumberSelectorConfig(min=0.5, max=10, step=0.5)
                    ),
                }
            )

        return self.async_show_form(step_id="serial", data_schema=data_schema, errors=errors)

    async def async_step_tcp(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Configure TCP access."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_PROTOCOL] = PROTOCOL_TCP
            try:
                info = await self.hass.async_add_executor_job(validate_and_connect, self.hass, user_input)
            except AuroraError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected Aurora TCP error during setup")
                errors["base"] = "cannot_connect"
            else:
                info.update(user_input)
                await self.async_set_unique_id(info[ATTR_SERIAL_NUMBER])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info[ATTR_SERIAL_NUMBER], data=info)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_ADDRESS, default=DEFAULT_ADDRESS): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_ADDRESS, max=MAX_ADDRESS)
                ),
                vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): NumberSelector(
                    NumberSelectorConfig(min=0.5, max=10, step=0.5)
                ),
            }
        )
        return self.async_show_form(step_id="tcp", data_schema=schema, errors=errors)


class AuroraABBOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        self._com_ports_list: list[str] | None = None
        self._default_com_port: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        protocol = self.config_entry.data[CONF_PROTOCOL]
        options = self.config_entry.options
        current = {**self.config_entry.data, **options}

        schema_dict: dict = {
            vol.Required(CONF_ADDRESS, default=current.get(CONF_ADDRESS, DEFAULT_ADDRESS)): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_ADDRESS, max=MAX_ADDRESS)
            ),
            vol.Required(CONF_TIMEOUT, default=float(current.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))): NumberSelector(
                NumberSelectorConfig(min=0.5, max=10, step=0.5)
            ),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=int(current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL_SECONDS,
                    max=MAX_SCAN_INTERVAL_SECONDS,
                    step=5,
                )
            ),
        }

        if protocol == PROTOCOL_TCP:
            schema_dict = {
                vol.Required(CONF_HOST, default=current.get(CONF_HOST, "")): cv.string,
                vol.Required(CONF_TCP_PORT, default=int(current.get(CONF_TCP_PORT, DEFAULT_TCP_PORT))): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                **schema_dict,
            }
        else:
            self._com_ports_list, self._default_com_port = await async_scan_comports(self.hass)
            if self._com_ports_list:
                schema_dict = {
                    vol.Required(CONF_PORT, default=current.get(CONF_PORT, self._default_com_port)): vol.In(
                        self._com_ports_list
                    ),
                    **schema_dict,
                }
            else:
                schema_dict = {
                    vol.Required(CONF_PORT, default=current.get(CONF_PORT, "/dev/ttyUSB0")): cv.string,
                    **schema_dict,
                }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema_dict))
