"""Secret Reader — runtime access to secrets.yaml with user restrictions."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError

from .const import ATTR_NAME, ATTR_VALUE, CONF_ALLOWED_USERS, DOMAIN, SERVICE_READ


def _load_secrets_yaml(path: str) -> dict:
    import yaml
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN] = entry

    async def _handle_read(call: ServiceCall) -> ServiceResponse:
        allowed: list[str] = entry.options.get(CONF_ALLOWED_USERS, [])
        user_id: str | None = call.context.user_id

        # System/automation calls (no user context) are always allowed.
        # Named users must appear in the allow-list once one is configured.
        if user_id is not None and allowed and user_id not in allowed:
            raise ServiceValidationError("Access denied: user not in allowed list")

        name: str = call.data[ATTR_NAME]
        path = hass.config.path("secrets.yaml")
        try:
            secrets = await hass.async_add_executor_job(_load_secrets_yaml, path)
        except FileNotFoundError:
            raise ServiceValidationError(
                "secrets.yaml not found in the Home Assistant config directory"
            )
        if name not in secrets:
            raise ServiceValidationError(f"Key '{name}' not found in secrets.yaml")
        return {ATTR_NAME: name, ATTR_VALUE: str(secrets[name])}

    hass.services.async_register(
        DOMAIN,
        SERVICE_READ,
        _handle_read,
        schema=vol.Schema({vol.Required(ATTR_NAME): str}),
        supports_response=SupportsResponse.ONLY,
    )

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.pop(DOMAIN, None)
    if hass.services.has_service(DOMAIN, SERVICE_READ):
        hass.services.async_remove(DOMAIN, SERVICE_READ)
    return True
