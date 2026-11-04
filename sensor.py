from __future__ import annotations

import math
import re

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, MODE_NAMES
from .entity import StoutPlusEntityMixin


SENSORS = [
    ("flow_temperature", "Flow temperature", "main", "ActValTempCarrier", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    # Temporarily disabled: duplicates the Flow temperature target control.
    # ("flow_temperature_target", "Flow temperature target", "main", "SetTempCarrier", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("room_temperature", "Room temperature", "main", "TempInRoom", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    # Temporarily disabled: duplicates the Room temperature target control.
    # ("room_temperature_target", "Room temperature target", "main", "setTempRoomMode", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("current_power", "Current power", "other", "CurrPwr_str", None, UnitOfPower.KILO_WATT),
    ("water_pressure", "Water pressure", "other", "ActPress", SensorDeviceClass.PRESSURE, "bar"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [StoutPlusSensor(coordinator, entry, *description) for description in SENSORS]
        + [
            StoutPlusModeSensor(coordinator, entry),
            StoutPlusErrorSensor(coordinator, entry),
            StoutPlusPumpSensor(coordinator, entry),
        ]
    )


class StoutPlusSensor(StoutPlusEntityMixin, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry,
        key: str,
        name: str,
        section: str,
        field: str,
        device_class,
        unit,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._section = section
        self._field = field
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._stout_suggested_object_id = f"stout_plus_{key}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_suggested_display_precision = 1
        if device_class == SensorDeviceClass.TEMPERATURE:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key in ("current_power", "water_pressure"):
            self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self):
        value = self.coordinator.data[self._section].get(self._field)
        if value is None or value == "":
            return None
        if self._field == "ActPress":
            match = re.search(r"[-+]?[0-9]*\.?[0-9]+", str(value))
            value = match.group(0) if match else None
        if self._field == "CurrPwr_str":
            value = str(value).replace("кВт", "").strip()
        try:
            result = float(value)
            return result if math.isfinite(result) else None
        except (TypeError, ValueError, OverflowError):
            return None


class StoutPlusModeSensor(StoutPlusEntityMixin, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Operating mode"
    _attr_icon = "mdi:heat-wave"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_operating_mode"
        self._stout_suggested_object_id = "stout_plus_operating_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self):
        value = self.coordinator.data["main"].get("setMode")
        try:
            return MODE_NAMES.get(int(value), "Unknown")
        except (TypeError, ValueError):
            return "Unknown"


class StoutPlusErrorSensor(StoutPlusEntityMixin, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Boiler error"
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_boiler_error"
        self._stout_suggested_object_id = "stout_plus_boiler_error"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self):
        value = self.coordinator.data["main"].get("Err_str", "")
        return re.sub(r"<[^>]+>", "", str(value)).strip() or "Unknown"


class StoutPlusPumpSensor(StoutPlusEntityMixin, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Pump status"
    _attr_icon = "mdi:pump"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pump_status"
        self._stout_suggested_object_id = "stout_plus_pump_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self):
        try:
            status = int(self.coordinator.data["other"].get("PmpStat", 0))
        except (TypeError, ValueError):
            return "Unknown"
        if not status & 0x2:
            return "Unavailable"
        return "On" if status & 0x1 else "Off"
