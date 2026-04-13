"""Sensor platform for Aurora ABB PowerOne TCP."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_SERIAL_NUMBER,
    EntityCategory,
    UnitOfCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_DEVICE_NAME, ATTR_FIRMWARE, ATTR_MODEL, DEFAULT_DEVICE_NAME, DOMAIN, MANUFACTURER
from .coordinator import AuroraAbbConfigEntry, AuroraAbbDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class AuroraSensorEntityDescription(SensorEntityDescription):
    """Description of an Aurora sensor."""


SENSOR_TYPES: tuple[AuroraSensorEntityDescription, ...] = (
    AuroraSensorEntityDescription(
        key="grid_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="grid_voltage",
    ),
    AuroraSensorEntityDescription(
        key="grid_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="grid_current",
    ),
    AuroraSensorEntityDescription(
        key="instantaneouspower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="power_output",
    ),
    AuroraSensorEntityDescription(
        key="grid_frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="grid_frequency",
    ),
    AuroraSensorEntityDescription(
        key="power_in_1",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="power_input_1",
        entity_registry_enabled_default=False,
    ),
    AuroraSensorEntityDescription(
        key="power_in_2",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="power_input_2",
        entity_registry_enabled_default=False,
    ),
    AuroraSensorEntityDescription(
        key="temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="temperature",
    ),
    AuroraSensorEntityDescription(
        key="voltage_in_1",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="voltage_input_1",
        entity_registry_enabled_default=False,
    ),
    AuroraSensorEntityDescription(
        key="current_in_1",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="current_input_1",
        entity_registry_enabled_default=False,
    ),
    AuroraSensorEntityDescription(
        key="voltage_in_2",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="voltage_input_2",
        entity_registry_enabled_default=False,
    ),
    AuroraSensorEntityDescription(
        key="current_in_2",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="current_input_2",
        entity_registry_enabled_default=False,
    ),
    AuroraSensorEntityDescription(
        key="r_iso",
        native_unit_of_measurement="MOhm",
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="r_iso",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AuroraSensorEntityDescription(
        key="i_leak_dcdc",
        native_unit_of_measurement=UnitOfCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="i_leak_dcdc",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AuroraSensorEntityDescription(
        key="i_leak_inverter",
        native_unit_of_measurement=UnitOfCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="i_leak_inverter",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AuroraSensorEntityDescription(
        key="totalenergy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_energy",
    ),
    AuroraSensorEntityDescription(
        key="alarm",
        translation_key="alarm",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass,
    config_entry: AuroraAbbConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator = config_entry.runtime_data
    data = config_entry.data
    entities = [AuroraSensor(coordinator, data, description) for description in SENSOR_TYPES]
    async_add_entities(entities)


class AuroraSensor(CoordinatorEntity[AuroraAbbDataUpdateCoordinator], SensorEntity):
    """Representation of a sensor on an Aurora ABB PowerOne inverter."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AuroraAbbDataUpdateCoordinator,
        data: Mapping[str, Any],
        entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description

        serial = str(data.get(ATTR_SERIAL_NUMBER) or "unknown")
        model = str(data.get(ATTR_MODEL) or "Aurora Inverter")
        firmware = str(data.get(ATTR_FIRMWARE) or "unknown")
        device_name = str(data.get(ATTR_DEVICE_NAME) or DEFAULT_DEVICE_NAME)

        self._attr_unique_id = f"{serial}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer=MANUFACTURER,
            model=model,
            name=device_name,
            sw_version=firmware,
        )

    @property
    def native_value(self):
        """Return sensor value from coordinator data."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self.entity_description.key)
