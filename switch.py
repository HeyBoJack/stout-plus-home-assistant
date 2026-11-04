from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import StoutPlusApiError
from .const import DOMAIN
from .entity import StoutPlusEntityMixin


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    async_add_entities([StoutPlusRelaySoundSwitch(coordinator, api, entry)])


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
