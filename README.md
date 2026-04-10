# Aurora ABB PowerOne TCP

Custom Home Assistant integration for ABB / Power-One Aurora inverters via:

- direct serial USB/RS485
- transparent RS485-over-TCP gateways

This repository adds TCP support on top of the Aurora transport support already present in `aurorapy`, while keeping a normal Home Assistant UI-based config flow.

## Features

- Home Assistant UI setup
- Serial or TCP connection mode
- Read-only polling of common inverter values
- HACS-ready repository layout
- English and German translations
- Options flow for timeout and polling interval

## Requirements

- Home Assistant
- HACS
- an ABB / Power-One Aurora inverter
- either:
  - a local USB/RS485 adapter, or
  - a transparent RS485-over-TCP gateway

Important: the TCP gateway must forward the Aurora serial protocol transparently. This integration does not turn Aurora into Modbus or SunSpec.

## Installation via HACS

1. Open HACS.
2. Go to **Integrations**.
3. Open the menu and choose **Custom repositories**.
4. Add your GitHub repository URL.
5. Choose category **Integration**.
6. Install **Aurora ABB PowerOne TCP**.
7. Restart Home Assistant.
8. Go to **Settings → Devices & Services → Add Integration**.
9. Search for **Aurora ABB PowerOne TCP**.

## Manual installation

Copy this folder into your Home Assistant configuration directory:

```text
custom_components/aurora_abb_powerone_tcp/
```

Then restart Home Assistant.

## Configuration

During setup choose one of these connection types:

### TCP

Use this for RS485-to-TCP gateways.

Example:
- Host: `172.17.3.17`
- TCP port: `2000`
- Inverter address: `2`
- Timeout: `1.0`

### Serial

Use this for a local USB/RS485 adapter.

Example:
- Serial port: `/dev/ttyUSB0`
- Inverter address: `2`
- Timeout: `1.0`

## Included sensors

- Grid voltage
- Grid current
- Power output
- Grid frequency
- Temperature
- Total energy
- DC input measurements
- Diagnostic leakage and insulation values
- Alarm state

## Options

After setup you can change:
- timeout
- polling interval
- TCP host / port
- serial port
- inverter address

## Scope

This first release is intentionally read-only. Output limiting and other write commands should only be added after the transport and model-specific protocol support are verified.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Disclaimer

Use at your own risk. Always verify values against the inverter display or the vendor tools before basing control logic on them.

## License

MIT
