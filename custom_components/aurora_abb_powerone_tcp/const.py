"""Constants for the Aurora ABB PowerOne TCP integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "aurora_abb_powerone_tcp"
PLATFORMS: list[Platform] = [Platform.SENSOR]

MIN_ADDRESS = 2
MAX_ADDRESS = 63
DEFAULT_ADDRESS = 2
DEFAULT_TCP_PORT = 2000
DEFAULT_TIMEOUT = 1.0
DEFAULT_SCAN_INTERVAL_SECONDS = 30
MIN_SCAN_INTERVAL_SECONDS = 5
MAX_SCAN_INTERVAL_SECONDS = 300

DEFAULT_INTEGRATION_TITLE = "PhotoVoltaic Inverters"
DEFAULT_DEVICE_NAME = "Solar Inverter"
MANUFACTURER = "ABB / Power-One"

ATTR_DEVICE_NAME = "device_name"
ATTR_FIRMWARE = "firmware"
ATTR_MODEL = "model"

CONF_PROTOCOL = "protocol"
CONF_HOST = "host"
CONF_TCP_PORT = "tcp_port"
CONF_TIMEOUT = "timeout"
CONF_SCAN_INTERVAL = "scan_interval"

PROTOCOL_SERIAL = "serial"
PROTOCOL_TCP = "tcp"
