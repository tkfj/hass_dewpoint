from __future__ import annotations
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.selector import (
    EntitySelector, EntitySelectorConfig, NumberSelector, NumberSelectorConfig
)

from .const import DOMAIN, CONF_NAME, CONF_TEMP_ENTITY, CONF_HUM_ENTITY, CONF_PRECISION

class DewPointConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME) or "Dew Point",
                data=user_input,
            )

        schema = vol.Schema({
            vol.Optional(CONF_NAME, default="Dew Point"): str,
            vol.Required(CONF_TEMP_ENTITY): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Required(CONF_HUM_ENTITY): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class="humidity")
            ),
            vol.Optional(CONF_PRECISION, default=1): NumberSelector(
                NumberSelectorConfig(min=0, max=3, step=1, mode="box")
            ),
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DewPointOptionsFlow(config_entry)

class DewPointOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.entry.data, **(self.entry.options or {})}
        schema = vol.Schema({
            vol.Optional(CONF_NAME, default=data.get(CONF_NAME, "Dew Point")): str,
            vol.Required(CONF_TEMP_ENTITY, default=data[CONF_TEMP_ENTITY]): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Required(CONF_HUM_ENTITY, default=data[CONF_HUM_ENTITY]): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class="humidity")
            ),
            vol.Optional(CONF_PRECISION, default=data.get(CONF_PRECISION, 1)): NumberSelector(
                NumberSelectorConfig(min=0, max=3, step=1, mode="box")
            ),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
