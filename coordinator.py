from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import StoutPlusApi, StoutPlusApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class StoutPlusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: StoutPlusApi,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.requested_mode: int | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            main, other = await self._async_fetch_data()
        except StoutPlusApiError as err:
            raise UpdateFailed(str(err)) from err

        return {
            "main": main,
            "other": other,
        }

    async def async_refresh_main_params(self) -> None:
        try:
            main = await self.api.async_get_main_params()
        except StoutPlusApiError as err:
            _LOGGER.warning("Fast mode refresh failed: %s", err)
            return

        if self.data is not None:
            self.data = {**self.data, "main": main}
            self.async_update_listeners()

    async def _async_fetch_data(
        self,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        main, other = await asyncio.gather(
            self.api.async_get_main_params(),
            self.api.async_get_other_params(),
        )
        return main, other
