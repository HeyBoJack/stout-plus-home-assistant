from __future__ import annotations

import math
from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import StoutPlusApiError
from .const import DOMAIN
from .entity import StoutPlusEntityMixin


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        StoutPlusScheduleTime(data["coordinator"], data["api"], entry, True),
        StoutPlusScheduleTime(data["coordinator"], data["api"], entry, False),
    ])


class StoutPlusScheduleTime(StoutPlusEntityMixin, CoordinatorEntity, TimeEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, api, entry: ConfigEntry, is_day: bool) -> None:
        super().__init__(coordinator)
        self._api = api
        self._is_day = is_day
        suffix = "day_start" if is_day else "night_start"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._stout_suggested_object_id = f"stout_plus_{suffix}"
        self._attr_name = "Mode time: Day" if is_day else "Mode time: Night"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_value(self) -> dt_time | None:
        other = self.coordinator.data.get("other", {})
        key = "dayTime" if self._is_day else "nightTime"
        value = other.get(key)
        if not isinstance(value, str):
            return None
        try:
            hour, minute = map(int, value.split(":"))
            return dt_time(hour, minute)
        except (ValueError, TypeError):
            return None

    async def async_set_value(self, value: dt_time) -> None:
        try:
            other = self.coordinator.data["other"]

            def power_kw(key: str) -> int:
                levels = float(other[key])
                full_power = float(other["FullPwr_str"])
                total_levels = float(other["PowerLevels_str"])

                if (
                    not all(math.isfinite(v) for v in (levels, full_power, total_levels))
                    or full_power <= 0
                    or total_levels <= 0
                ):
                    raise ValueError("Invalid boiler power parameters")

                return round(levels * full_power / total_levels)

            day_time = (
                value.strftime("%H:%M")
                if self._is_day
                else str(other["dayTime"])
            )
            night_time = (
                str(other["nightTime"])
                if self._is_day
                else value.strftime("%H:%M")
            )

            await self._api.async_set_power_schedule(
                day_power=power_kw("amountActiveLevelsPerDay"),
                night_power=power_kw("amountActiveLevelsAtNight"),
                day_time=day_time,
                night_time=night_time,
            )

        except StoutPlusApiError as err:
            raise HomeAssistantError(str(err)) from err
        except (KeyError, TypeError, ValueError, OverflowError) as err:
            raise HomeAssistantError(
                f"Invalid boiler power schedule data: {err}"
            ) from err

        await self.coordinator.async_request_refresh()
