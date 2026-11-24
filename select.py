from __future__ import annotations
import asyncio

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import StoutPlusApiError
from .const import DOMAIN, MODE_NAMES
from .entity import (
    StoutPlusEntityMixin,
    get_antilegionella_settings,
    antilegionella_available,
    dhw_settings_available,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            StoutPlusModeSelect(data["coordinator"], data["api"], entry),
            StoutPlusOutdoorTargetSelect(data["coordinator"], data["api"], entry),
            StoutPlusDhwPowerSelect(data["coordinator"], data["api"], entry),
            StoutPlusAlgorithmSelect(data["coordinator"], data["api"], entry, True),
            StoutPlusAlgorithmSelect(data["coordinator"], data["api"], entry, False),
            StoutPlusPumpLagSelect(data["coordinator"], data["api"], entry),
            StoutPlusAntilegionellaTemperatureSelect(data["coordinator"], data["api"], entry),
            StoutPlusAntilegionellaWeekdaySelect(data["coordinator"], data["api"], entry),
        ]
    )


class StoutPlusModeSelect(StoutPlusEntityMixin, CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Operating mode"
    _attr_icon = "mdi:hvac"
    _attr_options = list(MODE_NAMES.values())

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_operating_mode"
        self._stout_suggested_object_id = "stout_plus_operating_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def current_option(self) -> str | None:
        mode = self.coordinator.data["main"].get("setMode")
        try:
            return MODE_NAMES.get(int(mode))
        except (TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        mode = next(
            (key for key, value in MODE_NAMES.items() if value == option),
            None,
        )
        if mode is None:
            raise HomeAssistantError(f"Unsupported boiler mode: {option}")

        self.coordinator.requested_mode = mode
        self.coordinator.async_update_listeners()

        try:
            try:
                await self._api.async_set_mode(mode)
            except StoutPlusApiError as err:
                raise HomeAssistantError(
                    f"Failed to change boiler mode: {err}"
                ) from err

            for _ in range(20):
                await asyncio.sleep(1)
                await self.coordinator.async_refresh_main_params()
                current_mode = self.coordinator.data["main"].get("setMode")
                try:
                    if int(current_mode) == mode:
                        return
                except (TypeError, ValueError):
                    pass

            raise HomeAssistantError(
                f"Boiler did not confirm mode {option} within 20 seconds"
            )
        finally:
            self.coordinator.requested_mode = None
            self.coordinator.async_update_listeners()


class StoutPlusDhwPowerSelect(
    StoutPlusEntityMixin, CoordinatorEntity, SelectEntity
):
    _attr_has_entity_name = True
    _attr_name = "DHW power"
    _attr_icon = "mdi:lightning-bolt"
    _attr_options = [f"{power} kW" for power in range(2, 19, 2)]

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_dhw_power"
        self._stout_suggested_object_id = "stout_plus_dhw_power"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def available(self) -> bool:
        return super().available and dhw_settings_available(
            self.coordinator.data.get("main", {})
        )

    @property
    def current_option(self) -> str | None:
        value = self.coordinator.data.get("main", {}).get("DHWLevel")
        try:
            index = int(value) - 1
            return self._attr_options[index] if 0 <= index < len(self._attr_options) else None
        except (TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise HomeAssistantError(f"Unsupported DHW power: {option}")

        index = self._attr_options.index(option)
        try:
            await self._api.async_set_dhw_power(index)
        except (StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(str(err)) from err

        await self.coordinator.async_request_refresh()

class StoutPlusAlgorithmSelect(StoutPlusEntityMixin, CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_options = ["Slow", "Fast"]

    @property
    def available(self) -> bool:
        try:
            alg = int(self.coordinator.data["other"]["Alg"])
            return not bool(alg & 0x4)
        except (KeyError, TypeError, ValueError):
            return False

    def __init__(self, coordinator, api, entry: ConfigEntry, is_heating: bool) -> None:
        super().__init__(coordinator)
        self._api = api
        self._is_heating = is_heating
        suffix = "heating_algorithm" if is_heating else "dhw_algorithm"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._stout_suggested_object_id = f"stout_plus_{suffix}"
        self._attr_name = "Algorithm: heating" if is_heating else "Algorithm: DHW"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:fire" if is_heating else "mdi:water-boiler"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def current_option(self) -> str | None:
        try:
            alg = int(self.coordinator.data["other"]["Alg"])
            bit = 0 if self._is_heating else 1
            return "Fast" if (alg >> bit) & 1 else "Slow"
        except (KeyError, TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise HomeAssistantError(f"Unsupported algorithm: {option}")

        algorithm = 1 if option == "Fast" else 0
        try:
            if self._is_heating:
                await self._api.async_set_heating_algorithm(algorithm)
            else:
                await self._api.async_set_dhw_algorithm(algorithm)
        except StoutPlusApiError as err:
            raise HomeAssistantError(
                f"Failed to change algorithm: {err}"
            ) from err

        await self.coordinator.async_request_refresh()


class StoutPlusAntilegionellaTemperatureSelect(
    StoutPlusEntityMixin, CoordinatorEntity, SelectEntity
):
    _attr_has_entity_name = True
    _attr_name = "Antilegionella temperature"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:thermometer-water"
    _attr_options = ["60°C", "70°C"]

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_antilegionella_temperature"
        self._stout_suggested_object_id = "stout_plus_antilegionella_temperature"
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
    def current_option(self) -> str | None:
        try:
            _, temperature, _, _ = get_antilegionella_settings(
                self.coordinator.data.get("other", {})
            )
            return f"{temperature}°C"
        except (KeyError, TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise HomeAssistantError(
                f"Unsupported antilegionella temperature: {option}"
            )

        try:
            enabled, _, weekday, hour = get_antilegionella_settings(
                self.coordinator.data.get("other", {})
            )
            await self._api.async_set_antilegionella(
                enabled, int(option[:-2]), weekday, hour
            )
        except (KeyError, TypeError, StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(str(err)) from err

        await self.coordinator.async_request_refresh()


class StoutPlusAntilegionellaWeekdaySelect(
    StoutPlusEntityMixin, CoordinatorEntity, SelectEntity
):
    _attr_has_entity_name = True
    _attr_translation_key = "antilegionella_weekday"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:calendar-week"
    _attr_options = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_antilegionella_weekday"
        self._stout_suggested_object_id = "stout_plus_antilegionella_weekday"
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
    def current_option(self) -> str | None:
        try:
            _, _, weekday, _ = get_antilegionella_settings(
                self.coordinator.data.get("other", {})
            )
            return self._attr_options[weekday]
        except (KeyError, TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise HomeAssistantError(
                f"Unsupported antilegionella weekday: {option}"
            )

        try:
            enabled, temperature, _, hour = get_antilegionella_settings(
                self.coordinator.data.get("other", {})
            )
            await self._api.async_set_antilegionella(
                enabled, temperature, self._attr_options.index(option), hour
            )
        except (KeyError, TypeError, StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(str(err)) from err

        await self.coordinator.async_request_refresh()


class StoutPlusOutdoorTargetSelect(
    StoutPlusEntityMixin, CoordinatorEntity, SelectEntity
):
    _attr_has_entity_name = True
    _attr_name = "Outdoor target"
    _attr_icon = "mdi:thermometer-chevron-up"
    _attr_options = ["22", "25", "30", "35", "40", "45", "50", "55", "60"]

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_outdoor_target"
        self._stout_suggested_object_id = "stout_plus_outdoor_target"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def available(self) -> bool:
        try:
            return super().available and int(
                self.coordinator.data["main"]["setMode"]
            ) == 3
        except (KeyError, TypeError, ValueError):
            return False

    @property
    def current_option(self) -> str | None:
        try:
            index = int(self.coordinator.data["main"]["SetDepNumber"])
            return self._attr_options[index] if 0 <= index < 9 else None
        except (KeyError, TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise HomeAssistantError(f"Unsupported outdoor target: {option}")

        try:
            await self._api.async_set_outdoor_target(
                self._attr_options.index(option)
            )
        except (StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(
                f"Failed to change outdoor target: {err}"
            ) from err

        await self.coordinator.async_request_refresh()


class StoutPlusPumpLagSelect(StoutPlusEntityMixin, CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "pump_overrun"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:pump"
    _attr_options = [
        "continuous",
        "five_minutes",
        "ten_minutes",
        "fifteen_minutes",
    ]

    def __init__(self, coordinator, api, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_pump_lag"
        self._stout_suggested_object_id = "stout_plus_pump_lag"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def available(self) -> bool:
        try:
            pump_lag = int(self.coordinator.data["other"]["PumpLag"])
            return bool(pump_lag & 0x80)
        except (KeyError, TypeError, ValueError):
            return False

    @property
    def current_option(self) -> str | None:
        try:
            index = int(self.coordinator.data["other"]["PumpLag"]) & 0x7F
            return self._attr_options[index] if 0 <= index < len(self._attr_options) else None
        except (KeyError, TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise HomeAssistantError(f"Unsupported pump overrun: {option}")

        try:
            await self._api.async_set_pump_lag(option)
        except StoutPlusApiError as err:
            raise HomeAssistantError(
                f"Failed to change pump overrun: {err}"
            ) from err

        await self.coordinator.async_request_refresh()
