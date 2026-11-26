from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import StoutPlusApi, StoutPlusApiError
from .const import DEFAULT_PORT, DOMAIN


class StoutPlusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            api = StoutPlusApi(
                async_get_clientsession(self.hass),
                host=host,
                port=port,
            )

            try:
                await api.async_get_main_params()
                await api.async_get_other_params()
            except StoutPlusApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="STOUT PLUS",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): vol.All(
                    str, vol.Strip, vol.Length(min=1)
                ),
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
