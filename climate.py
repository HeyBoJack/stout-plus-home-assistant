from __future__ import annotations

import asyncio
import math

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
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

    async_add_entities(
        [StoutPlusClimate(data["coordinator"], data["api"], entry)]
    )


class StoutPlusClimate(StoutPlusEntityMixin, CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = "Room thermostat"
    _attr_icon = "mdi:thermostat"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 0
    _attr_max_temp = 35
    _attr_target_temperature_step = 0.1
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api

        self._attr_unique_id = f"{entry.entry_id}_room_climate"
        self._stout_suggested_object_id = "stout_plus_room_thermostat"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def native_current_temperature(self) -> float | None:
        value = self.coordinator.data["main"].get("TempInRoom")
	try:
            result = float(value) if value is not None else None
            return result if result is not None and math.isfinite(result) else None
        except (TypeError, ValueError):
            return None

    @property
    def native_target_temperature(self) -> float | None:
        value = self.coordinator.data["main"].get("setTempRoomMode")
        try:
            result = float(value) if value is not None else None
            return result if result is not None and math.isfinite(result) else None
        except (TypeError, ValueError):
            return None

    @property
    def hvac_mode(self) -> HVACMode | None:
        try:
            mode = int(self.coordinator.data["main"].get("setMode"))
        except (TypeError, ValueError):
            return None

        return HVACMode.HEAT if mode == 2 else None

    @property
    def available(self) -> bool:
        try:
            return (
                super().available
                and int(self.coordinator.data["main"].get("setMode")) == 2
            )
        except (TypeError, ValueError):
            return False

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get("temperature")

        if temperature is None:
            return

        try:
            temperature = float(temperature)
        except (TypeError, ValueError, OverflowError):
            raise HomeAssistantError("Invalid room temperature")

        if not math.isfinite(temperature) or not 0 <= temperature <= 35:
            raise HomeAssistantError(
                "Room temperature must be between 0 and 35 °C"
            )

        try:
            await self._api.async_set_room_temperature(temperature)
        except (StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(
                f"Failed to set room temperature: {err}"
            ) from err

        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode != HVACMode.HEAT:
            raise HomeAssistantError(
                "Only Room heating mode is supported by this thermostat"
            )

        if self.hvac_mode != HVACMode.HEAT:
            try:
                await self._api.async_set_mode(2)
            except (StoutPlusApiError, ValueError) as err:
                raise HomeAssistantError(
                    f"Failed to enable Room mode: {err}"
                ) from err

            for _ in range(20):
                if not await self.coordinator.async_refresh_main_params():
                    await asyncio.sleep(1)
                    continue

                if self.hvac_mode == HVACMode.HEAT:
                    return

                await asyncio.sleep(1)

            raise HomeAssistantError(
                "Boiler did not confirm Room mode within 20 seconds"
            )
