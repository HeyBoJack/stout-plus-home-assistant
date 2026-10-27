from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [StoutPlusMaxFlowTemperatureNumber(data["coordinator"], data["api"], entry), StoutPlusTemperatureAccuracyNumber(data["coordinator"], data["api"], entry), StoutPlusFlowTemperatureNumber(data["coordinator"], data["api"], entry), StoutPlusRoomTemperatureNumber(data["coordinator"], data["api"], entry), StoutPlusDayPowerNumber(data["coordinator"], data["api"], entry), StoutPlusNightPowerNumber(data["coordinator"], data["api"], entry)]
    )


class StoutPlusMaxFlowTemperatureNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Maximum flow temperature"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:thermometer-alert"
    _attr_native_min_value = 20
    _attr_native_max_value = 85
    _attr_native_step = 1
    _attr_mode = "box"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_max_flow_temperature"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get("other", {}).get("SetMaxTempCarrier")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        if not 20 <= value <= 85:
            raise ValueError("Maximum flow temperature must be between 20 and 85 °C")
        await self._api.async_set_max_flow_temperature(value)
        await self.coordinator.async_request_refresh()

class StoutPlusTemperatureAccuracyNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Flow temperature accuracy"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:thermometer-check"
    _attr_native_min_value = 0.4
    _attr_native_max_value = 3.0
    _attr_native_step = 0.1
    _attr_mode = "box"

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_temperature_accuracy"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get("other", {}).get("gist")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        if not 0.4 <= value <= 3.0:
            raise ValueError("Temperature accuracy must be between 0.4 and 3.0")
        await self._api.async_set_temperature_accuracy(value)
        await self.coordinator.async_request_refresh()

class StoutPlusFlowTemperatureNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Flow temperature target"
    _attr_icon = "mdi:thermometer-chevron-up"
    _attr_native_min_value = 8
    _attr_native_max_value = 85
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_flow_temperature_target"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data["main"].get("SetTempCarrier")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        requested_mode = getattr(self.coordinator, "requested_mode", None)
        actual_mode = self.coordinator.data["main"].get("setMode")
        try:
            if requested_mode is not None and int(requested_mode) != 0:
                return False
            return super().available and int(actual_mode) == 0
        except (TypeError, ValueError):
            return False

    async def async_set_native_value(self, value: float) -> None:
        if not 8 <= value <= 85:
            raise ValueError("Flow temperature must be between 8 and 85 °C")

        await self._api.async_set_flow_temperature(value)
        await self.coordinator.async_request_refresh()


class StoutPlusRoomTemperatureNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Room temperature target"
    _attr_icon = "mdi:thermostat"
    _attr_native_min_value = 0
    _attr_native_max_value = 35
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_room_temperature_target"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data["main"].get("setTempRoomMode")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        requested_mode = getattr(self.coordinator, "requested_mode", None)
        actual_mode = self.coordinator.data["main"].get("setMode")
        try:
            if requested_mode is not None and int(requested_mode) != 2:
                return False
            return super().available and int(actual_mode) == 2
        except (TypeError, ValueError):
            return False

    async def async_set_native_value(self, value: float) -> None:
        if not 0 <= value <= 35:
            raise ValueError("Room temperature must be between 0 and 35 °C")

        await self._api.async_set_room_temperature(value)
        await self.coordinator.async_request_refresh()


class StoutPlusPowerNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = 2
    _attr_native_max_value = 18
    _attr_native_step = 2
    _attr_native_unit_of_measurement = "kW"
    _attr_mode = "slider"

    def __init__(self, coordinator, api, entry: ConfigEntry, is_day: bool) -> None:
        super().__init__(coordinator)
        self._api = api
        self._is_day = is_day
        suffix = "day" if is_day else "night"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}_power"
        self._attr_name = "Power: Day" if is_day else "Power: Night"
        self._attr_icon = "mdi:flash"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self) -> float | None:
        other = self.coordinator.data.get("other", {})
        try:
            levels = float(other[
                "amountActiveLevelsPerDay" if self._is_day
                else "amountActiveLevelsAtNight"
            ])
            full_power = float(other["FullPwr_str"])
            total_levels = float(other["PowerLevels_str"])
            if total_levels <= 0:
                return None
            return round(levels * full_power / total_levels, 1)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        if not 2 <= value <= 18 or value % 2:
            raise ValueError("Power must be 2–18 kW in steps of 2 kW")

        other = self.coordinator.data["other"]

        def power_kw(key: str) -> int:
            levels = float(other[key])
            full_power = float(other["FullPwr_str"])
            total_levels = float(other["PowerLevels_str"])
            return round(levels * full_power / total_levels)

        day_power = int(value) if self._is_day else power_kw("amountActiveLevelsPerDay")
        night_power = int(value) if not self._is_day else power_kw("amountActiveLevelsAtNight")

        await self._api.async_set_power_schedule(
            day_levels=day_power,
            night_levels=night_power,
            day_time=str(other["dayTime"]),
            night_time=str(other["nightTime"]),
        )
        await self.coordinator.async_request_refresh()


class StoutPlusDayPowerNumber(StoutPlusPowerNumber):
    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator, api, entry, is_day=True)


class StoutPlusNightPowerNumber(StoutPlusPowerNumber):
    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator, api, entry, is_day=False)
