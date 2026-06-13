"""Tests for the secret_reader.read service."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import Context, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError

from custom_components.secret_reader.const import DOMAIN, SERVICE_READ

_SECRETS = {"api_key": "abc123", "pin": "0815"}

_PATCH = "custom_components.secret_reader._load_secrets_yaml"


async def _setup(hass: HomeAssistant, entry) -> None:
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


# ---------------------------------------------------------------------------
# Config flow
# ---------------------------------------------------------------------------


class TestConfigFlow:
    async def test_creates_entry(self, hass: HomeAssistant):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Secret Reader"

    async def test_single_instance_only(self, hass: HomeAssistant, entry):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "single_instance_allowed"


# ---------------------------------------------------------------------------
# Service: unrestricted access
# ---------------------------------------------------------------------------


class TestServiceUnrestricted:
    async def test_system_call_returns_value(self, hass: HomeAssistant, entry):
        """No user context (automation/system) → always allowed."""
        await _setup(hass, entry)
        with patch(_PATCH, return_value=_SECRETS):
            response = await hass.services.async_call(
                DOMAIN, SERVICE_READ, {"name": "api_key"},
                blocking=True, return_response=True,
            )
        assert response["name"] == "api_key"
        assert response["value"] == "abc123"

    async def test_empty_allowlist_permits_any_user(self, hass: HomeAssistant, entry):
        """allowed_users=[] means no restriction."""
        await _setup(hass, entry)
        user = await hass.auth.async_create_user("any_user")
        with patch(_PATCH, return_value=_SECRETS):
            response = await hass.services.async_call(
                DOMAIN, SERVICE_READ, {"name": "api_key"},
                blocking=True, return_response=True,
                context=Context(user_id=user.id),
            )
        assert response["value"] == "abc123"

    async def test_missing_key_raises(self, hass: HomeAssistant, entry):
        await _setup(hass, entry)
        with patch(_PATCH, return_value=_SECRETS):
            with pytest.raises(ServiceValidationError):
                await hass.services.async_call(
                    DOMAIN, SERVICE_READ, {"name": "no_such_key"},
                    blocking=True, return_response=True,
                )

    async def test_missing_file_raises(self, hass: HomeAssistant, entry):
        await _setup(hass, entry)
        with patch(_PATCH, side_effect=FileNotFoundError):
            with pytest.raises(ServiceValidationError):
                await hass.services.async_call(
                    DOMAIN, SERVICE_READ, {"name": "api_key"},
                    blocking=True, return_response=True,
                )


# ---------------------------------------------------------------------------
# Service: user restrictions
# ---------------------------------------------------------------------------


class TestServiceUserRestrictions:
    async def _entry_with_users(self, hass: HomeAssistant, allowed_ids: list[str]):
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        from custom_components.secret_reader.const import CONF_ALLOWED_USERS
        e = MockConfigEntry(
            domain=DOMAIN,
            data={},
            options={CONF_ALLOWED_USERS: allowed_ids},
            unique_id=DOMAIN,
            title="Secret Reader",
        )
        e.add_to_hass(hass)
        await hass.config_entries.async_setup(e.entry_id)
        await hass.async_block_till_done()
        return e

    async def test_allowed_user_gets_value(self, hass: HomeAssistant):
        user = await hass.auth.async_create_user("alice")
        await self._entry_with_users(hass, [user.id])
        with patch(_PATCH, return_value=_SECRETS):
            response = await hass.services.async_call(
                DOMAIN, SERVICE_READ, {"name": "api_key"},
                blocking=True, return_response=True,
                context=Context(user_id=user.id),
            )
        assert response["value"] == "abc123"

    async def test_unlisted_user_is_denied(self, hass: HomeAssistant):
        alice = await hass.auth.async_create_user("alice")
        bob = await hass.auth.async_create_user("bob")
        await self._entry_with_users(hass, [alice.id])
        with patch(_PATCH, return_value=_SECRETS):
            with pytest.raises(ServiceValidationError):
                await hass.services.async_call(
                    DOMAIN, SERVICE_READ, {"name": "api_key"},
                    blocking=True, return_response=True,
                    context=Context(user_id=bob.id),
                )

    async def test_system_call_bypasses_restriction(self, hass: HomeAssistant):
        """Even with an allowlist, system calls (no user_id) are always allowed."""
        alice = await hass.auth.async_create_user("alice")
        await self._entry_with_users(hass, [alice.id])
        with patch(_PATCH, return_value=_SECRETS):
            response = await hass.services.async_call(
                DOMAIN, SERVICE_READ, {"name": "api_key"},
                blocking=True, return_response=True,
                # No context → user_id is None
            )
        assert response["value"] == "abc123"
