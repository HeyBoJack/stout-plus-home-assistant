from __future__ import annotations

import math
from collections.abc import Awaitable
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import StoutPlusApiError
from .const import DOMAIN
from .entity import (
    StoutPlusEntityMixin,
    get_antilegionella_settings,
    antilegionella_available,
)


async def _async_api_call(call: Awaitable[None]) -> None:
    try:
        await call
    except (StoutPlusApiError, ValueError) as err:
        raise HomeAssistantError(str(err)) from err


def _power_kw(other: dict[str, Any], key: str) -> int:
    try:
        levels = float(other[key])
        full_power = float(other["FullPwr_str"])
        total_levels = float(other["PowerLevels_str"])

        if (
            not math.isfinite(levels)
            or not math.isfinite(full_power)
            or not math.isfinite(total_levels)
            or full_power <= 0
            or total_levels <= 0
        ):
            raise ValueError("Invalid boiler power parameters")

        return round(levels * full_power / total_levels)
    except (KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError) as err:
        raise HomeAssistantError(
            f"Invalid boiler power schedule data: {err}"
        ) from err


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            StoutPlusMaxFlowTemperatureNumber(data["coordinator"], data["api"], entry),
            StoutPlusTemperatureAccuracyNumber(data["coordinator"], data["api"], entry),
            StoutPlusFlowTemperatureNumber(data["coordinator"], data["api"], entry),
            StoutPlusRoomTemperatureNumber(data["coordinator"], data["api"], entry),
            StoutPlusDayPowerNumber(data["coordinator"], data["api"], entry),
            StoutPlusNightPowerNumber(data["coordinator"], data["api"], entry),
            StoutPlusAntilegionellaHourNumber(data["coordinator"], data["api"], entry),
        ]
    )


class StoutPlusMaxFlowTemperatureNumber(StoutPlusEntityMixin, CoordinatorEntity, NumberEntity):
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
        self._stout_suggested_object_id = "stout_plus_max_flow_temperature"
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
        await _async_api_call(self._api.async_set_max_flow_temperature(value))
        await self.coordinator.async_request_refresh()

class StoutPlusTemperatureAccuracyNumber(StoutPlusEntityMixin, CoordinatorEntity, NumberEntity):
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
        self._stout_suggested_object_id = "stout_plus_temperature_accuracy"
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
        await _async_api_call(self._api.async_set_temperature_accuracy(value))
        await self.coordinator.async_request_refresh()

class StoutPlusFlowTemperatureNumber(StoutPlusEntityMixin, CoordinatorEntity, NumberEntity):
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
        self._stout_suggested_object_id = "stout_plus_flow_temperature_target"
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

        await _async_api_call(self._api.async_set_flow_temperature(value))
        await self.coordinator.async_request_refresh()


class StoutPlusRoomTemperatureNumber(StoutPlusEntityMixin, CoordinatorEntity, NumberEntity):
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
        self._stout_suggested_object_id = "stout_plus_room_temperature_target"
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

        await _async_api_call(self._api.async_set_room_temperature(value))
        await self.coordinator.async_request_refresh()


class StoutPlusAntilegionellaHourNumber(
    StoutPlusEntityMixin, CoordinatorEntity, NumberEntity
):
    _attr_has_entity_name = True
    _attr_name = "Antilegionella start hour"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = 23
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _attr_mode = "box"

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_antilegionella_hour"
        self._stout_suggested_object_id = "stout_plus_antilegionella_hour"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def available(self) -> bool:
        return super().available and antilegionella_available(
            self.coordinator.data.get("other", {})
        )

    @property
    def native_value(self) -> float | None:
        try:
            _, _, _, hour = get_antilegionella_settings(
                self.coordinator.data.get("other", {})
            )
            return float(hour)
        except (KeyError, TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        if (
            not math.isfinite(value)
            or not value.is_integer()
            or not 0 <= value <= 23
        ):
            raise ValueError(
                "Antilegionella start hour must be an integer between 0 and 23"
            )

        try:
            enabled, temperature, weekday, _ = get_antilegionella_settings(
                self.coordinator.data.get("other", {})
            )
            await self._api.async_set_antilegionella(
                enabled, temperature, weekday, int(value)
            )
        except (KeyError, TypeError, StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(str(err)) from err

        await self.coordinator.async_request_refresh()


class StoutPlusPowerNumber(StoutPlusEntityMixin, CoordinatorEntity, NumberEntity):
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
        self._stout_suggested_object_id = f"stout_plus_{suffix}_power"
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
            if (
                not all(math.isfinite(v) for v in (levels, full_power, total_levels))
                or full_power <= 0
                or total_levels <= 0
            ):
                return None
            return round(levels * full_power / total_levels, 1)
        except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        if not math.isfinite(value) or not 2 <= value <= 18 or value % 2:
            raise HomeAssistantError("Power must be 2–18 kW in steps of 2 kW")

        try:
            other = self.coordinator.data["other"]
            day_power = (
                int(value)
                if self._is_day
                else _power_kw(other, "amountActiveLevelsPerDay")
            )
            night_power = (
                int(value)
                if not self._is_day
                else _power_kw(other, "amountActiveLevelsAtNight")
            )

            await _async_api_call(
                self._api.async_set_power_schedule(
                    day_power=day_power,
                    night_power=night_power,
                    day_time=str(other["dayTime"]),
                    night_time=str(other["nightTime"]),
                )
            )
        except (KeyError, TypeError, ValueError, OverflowError) as err:
            raise HomeAssistantError(
                f"Invalid boiler power schedule data: {err}"
            ) from err

        await self.coordinator.async_request_refresh()


class StoutPlusDayPowerNumber(StoutPlusPowerNumber):
    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator, api, entry, is_day=True)


class StoutPlusNightPowerNumber(StoutPlusPowerNumber):
    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator, api, entry, is_day=False)
