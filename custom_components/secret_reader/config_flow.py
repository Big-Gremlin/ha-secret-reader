"""Config flow for Secret Reader."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_ALLOWED_USERS, DOMAIN


class SecretReaderConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-instance config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Secret Reader", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SecretReaderOptionsFlow()


class SecretReaderOptionsFlow(OptionsFlow):
    """Select which users may call the read service."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        all_users = await self.hass.auth.async_get_users()
        real_users = [u for u in all_users if not u.system_generated]
        current = self.config_entry.options.get(CONF_ALLOWED_USERS, [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_ALLOWED_USERS, default=current): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=u.id, label=u.name)
                                for u in real_users
                            ],
                            multiple=True,
                        )
                    )
                }
            ),
        )
