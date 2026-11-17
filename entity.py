from __future__ import annotations


class StoutPlusEntityMixin:
    _stout_suggested_object_id: str

    @property
    def suggested_object_id(self) -> str | None:
        return self._stout_suggested_object_id


def get_antilegionella_settings(other: dict) -> tuple[bool, int, int, int]:
    try:
        enabled_index = int(other["Antil_trn"])
        temperature_index = int(other["Antil_temp"])
        weekday = int(other["Antil_wday_str"])
        hour = int(other["set_time_legionella"])
    except (KeyError, TypeError, ValueError) as err:
        raise ValueError(f"Invalid antilegionella settings: {err}") from err

    if enabled_index not in (0, 1):
        raise ValueError("Invalid antilegionella enabled value")
    if temperature_index not in (0, 1):
        raise ValueError("Invalid antilegionella temperature value")
    if weekday not in range(7):
        raise ValueError("Invalid antilegionella weekday value")
    if hour not in range(24):
        raise ValueError("Invalid antilegionella hour value")

    return enabled_index == 1, 60 if temperature_index == 0 else 70, weekday, hour


def antilegionella_available(other: dict) -> bool:
    try:
        return int(other["exManagMode"]) == 0
    except (KeyError, TypeError, ValueError):
        return False
