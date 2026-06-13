"""Shared test fixtures."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.secret_reader.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def entry(hass):
    e = MockConfigEntry(
        domain=DOMAIN, data={}, options={}, unique_id=DOMAIN, title="Secret Reader"
    )
    e.add_to_hass(hass)
    return e


@pytest.fixture
async def setup_integration(hass, entry):
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
