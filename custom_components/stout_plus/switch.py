from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import StoutPlusApiError
from .const import DOMAIN
from .entity import (
    StoutPlusEntityMixin,
    get_antilegionella_settings,
    antilegionella_available,
    dhw_control_available,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    async_add_entities(
        [
            StoutPlusRelaySoundSwitch(coordinator, api, entry),
            StoutPlusDhwSwitch(coordinator, api, entry),
            StoutPlusAntilegionellaSwitch(coordinator, api, entry),
        ]
    )


class StoutPlusDhwSwitch(
    StoutPlusEntityMixin, CoordinatorEntity, SwitchEntity
):
    _attr_has_entity_name = True
    _attr_name = "DHW"
    _attr_icon = "mdi:water-boiler"

    def __init__(self, coordinator, api, entry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_dhw"
        self._stout_suggested_object_id = "stout_plus_dhw"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def available(self) -> bool:
        return super().available and dhw_control_available(
            self.coordinator.data.get("main", {})
        )

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get("main", {}).get("settedDHWmode")
        if value is None:
            return None
        try:
            return int(value) == 1
        except (TypeError, ValueError):
            return None

    async def _set_state(self, enabled: bool) -> None:
        try:
            await self._api.async_set_dhw_mode(enabled)
        except (StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(str(err)) from err

        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_state(False)

class StoutPlusAntilegionellaSwitch(
    StoutPlusEntityMixin, CoordinatorEntity, SwitchEntity
):
    _attr_has_entity_name = True
    _attr_name = "Antilegionella"
    _attr_icon = "mdi:water-thermometer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, api, entry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_antilegionella"
        self._stout_suggested_object_id = "stout_plus_antilegionella"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def is_on(self) -> bool | None:
        try:
            enabled, _, _, _ = get_antilegionella_settings(
                self.coordinator.data.get("other", {})
            )
            return enabled
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        return super().available and antilegionella_available(
            self.coordinator.data.get("other", {})
        )

    async def _set_state(self, enabled: bool) -> None:
        try:
            _, temperature, weekday, hour = get_antilegionella_settings(
                self.coordinator.data.get("other", {})
            )
            await self._api.async_set_antilegionella(
                enabled, temperature, weekday, hour
            )
        except (KeyError, TypeError, StoutPlusApiError, ValueError) as err:
            raise HomeAssistantError(str(err)) from err

        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_state(False)


class StoutPlusRelaySoundSwitch(StoutPlusEntityMixin, CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Relay sound signal"
    _attr_icon = "mdi:volume-high"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, api, entry) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_relay_sound"
        self._stout_suggested_object_id = "stout_plus_relay_sound"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="STOUT PLUS",
            manufacturer="STOUT",
            model="SEB-2201-000018",
        )

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get("other", {}).get("warn")
        if value is None:
            return None
        try:
            return int(value) == 1
        except (TypeError, ValueError):
            return None

    async def _set_state(self, enabled: bool) -> None:
        try:
            await self._api.async_set_relay_sound(enabled)
        except StoutPlusApiError as err:
            raise HomeAssistantError(str(err)) from err

        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_state(False)
