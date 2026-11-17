from __future__ import annotations

import asyncio
import json
import math
from typing import Any

import aiohttp

from .const import MODE_NAMES


class StoutPlusApi:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = 80,
        timeout: int = 10,
    ) -> None:
        self._session = session
        self._base_url = f"http://{host}:{port}"
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _get_json(self, endpoint: str) -> dict[str, Any]:
        url = f"{self._base_url}/{endpoint}"

        try:
            async with self._session.get(
                url,
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot read {endpoint}: {err}"
            ) from err
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise StoutPlusApiError(
                f"Invalid JSON from {endpoint}: {err}"
            ) from err

        if not isinstance(data, dict):
            raise StoutPlusApiError(
                f"Unexpected response from {endpoint}: expected JSON object"
            )

        return data

    async def async_get_main_params(self) -> dict[str, Any]:
        return await self._get_json("main_params")

    async def async_get_other_params(self) -> dict[str, Any]:
        return await self._get_json("other_params")

    async def async_set_mode(self, mode: int) -> None:
        if mode not in MODE_NAMES:
            raise ValueError(f"Unsupported boiler mode: {mode}")

        url = f"{self._base_url}/switch_mode"

        try:
            async with self._session.post(
                url,
                json=[mode],
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set boiler mode: {err}"
            ) from err


    async def async_set_room_temperature(self, temperature: float) -> None:
        if not math.isfinite(temperature) or not 0 <= temperature <= 35:
            raise ValueError("Room temperature must be between 0 and 35 °C")


        url = f"{self._base_url}/change_rmtrg"

        try:
            async with self._session.post(
                url,
                json=[temperature],
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set room temperature: {err}"
            ) from err

    async def async_set_flow_temperature(self, temperature: float) -> None:
        if not math.isfinite(temperature) or not 8 <= temperature <= 85:
            raise ValueError("Flow temperature must be between 8 and 85 °C")

        url = f"{self._base_url}/change_crrtrg"

        try:
            async with self._session.post(
                url,
                json=[temperature],
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set flow temperature: {err}"
            ) from err


    async def async_set_relay_sound(self, enabled: bool) -> None:
        try:
            async with self._session.post(
                f"{self._base_url}/switch_voice",
                data=f"[{1 if enabled else 0}]",
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set relay sound: {err}"
            ) from err


    async def async_set_temperature_accuracy(self, accuracy: float) -> None:
        if not math.isfinite(accuracy) or not 0.4 <= accuracy <= 3.0:
            raise ValueError(
                "Heat transfer fluid temperature accuracy must be between 0.4 and 3.0"
            )

        try:
            async with self._session.post(
                f"{self._base_url}/change_gist",
                json=[round(accuracy, 1)],
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set heat transfer fluid temperature accuracy: {err}"
            ) from err

    async def async_set_power_schedule(
        self,
        day_power: int,
        night_power: int,
        day_time: str,
        night_time: str,
    ) -> None:
        if not (
            2 <= day_power <= 18
            and day_power % 2 == 0
            and 2 <= night_power <= 18
            and night_power % 2 == 0
        ):
            raise ValueError("Power must be between 2 and 18 kW in steps of 2 kW")

        url = f"{self._base_url}/apply_power_day"
        data = {
            "amountActiveLevelsPerDay": f"{day_power:.1f} кВт",
            "amountActiveLevelsAtNight": f"{night_power:.1f} кВт",
            "dayTime": day_time,
            "nightTime": night_time,
        }

        try:
            async with self._session.post(
                url,
                data=data,
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set power schedule: {err}"
            ) from err


    async def async_set_pump_lag(self, option: str) -> None:
        values = {
            "continuous": "Постоянная работа",
            "five_minutes": "выбег 5 мин",
            "ten_minutes": "выбег 10 мин",
            "fifteen_minutes": "выбег 15 мин",
        }
        if option not in values:
            raise ValueError(f"Unsupported pump lag: {option}")
        option = values[option]

        try:
            async with self._session.post(
                f"{self._base_url}/apply_other_page",
                data={"PmpLag": option, "_acuri": "/set_add_data"},
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set pump lag: {err}"
            ) from err


    async def async_set_max_flow_temperature(self, temperature: float) -> None:
        if not math.isfinite(temperature) or not 20 <= temperature <= 85:
            raise ValueError("Maximum flow temperature must be between 20 and 85 °C")

        try:
            async with self._session.post(
                f"{self._base_url}/apply_other_page",
                data={
                    "SetMaxTempCarrier": f"{temperature:.1f}",
                    "_acuri": "/set_add_data",
                },
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set maximum flow temperature: {err}"
            ) from err

    async def async_set_heating_algorithm(self, algorithm: int) -> None:
        await self._async_set_algorithm("switch_heatalg", algorithm)

    async def async_set_dhw_algorithm(self, algorithm: int) -> None:
        await self._async_set_algorithm("switch_dhwalg", algorithm)

    async def _async_set_algorithm(self, endpoint: str, algorithm: int) -> None:
        if algorithm not in (0, 1):
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        url = f"{self._base_url}/{endpoint}"
        try:
            async with self._session.post(
                url, json=[algorithm], timeout=self._timeout
            ) as response:
                response.raise_for_status()
                await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set {endpoint}: {err}"
            ) from err


    async def async_set_antilegionella(
        self, enabled: bool, temperature: int, weekday: int, hour: int
    ) -> None:
        if temperature not in (60, 70):
            raise ValueError("Antilegionella temperature must be 60 or 70 °C")
        if weekday not in range(7):
            raise ValueError("Antilegionella weekday must be between 0 and 6")
        if hour not in range(24):
            raise ValueError("Antilegionella hour must be between 0 and 23")

        weekdays = (
            "Понедельник", "Вторник", "Среда", "Четверг",
            "Пятница", "Суббота", "Воскресенье",
        )
        data = {
            "Antil_trn": "Включен" if enabled else "Выключен",
            "Antil_temp": f"{temperature}°C",
            "Antil_wday_str": weekdays[weekday],
            "set_time_legionella": str(hour),
            "_acuri": "/set_add_data",
        }

        try:
            async with self._session.post(
                f"{self._base_url}/apply_alig_page",
                data=data,
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise StoutPlusApiError(
                f"Cannot set antilegionella: {err}"
            ) from err


class StoutPlusApiError(Exception):
    """Error communicating with the STOUT PLUS boiler."""
