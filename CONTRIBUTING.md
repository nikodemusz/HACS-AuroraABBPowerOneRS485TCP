# Contributing

Thanks for contributing.

## Local development

1. Clone the repository.
2. Copy `custom_components/aurora_abb_powerone_tcp` into your Home Assistant test instance under `config/custom_components/`.
3. Restart Home Assistant.
4. Add the integration in **Settings → Devices & Services**.

## Before opening a pull request

- Keep changes focused.
- Test both config flow and regular polling if your hardware allows it.
- Update translations when changing user-visible strings.
- Update the changelog for user-facing changes.

## Coding notes

- Keep the integration read-only unless the write command has been verified on real hardware.
- Prefer adding new measurements as disabled-by-default entities first.
- Avoid breaking the stored config entry schema.

## Reporting bugs

Please use the bug report template and include:
- inverter model
- transport type
- gateway model
- Home Assistant version
- logs with debug enabled for this integration and `aurorapy`
