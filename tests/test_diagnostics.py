"""Tests for diagnostics redaction and snapshot serialization."""

import json

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.homeassistant_ems.const import (
    CONF_BATTERIES,
    CONF_BATTERY_ID,
    CONF_BATTERY_NAME,
    CONF_BATTERY_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
    CONF_INVERTER_ID,
    CONF_INVERTER_NAME,
    CONF_INVERTER_POWER_ENTITY,
    CONF_INVERTERS,
    CONF_SITE_ENTITIES,
    CONF_SITE_NAME,
    DOMAIN,
    KEY_ELECTRICITY_PRICE,
    KEY_GRID_POWER,
)
from custom_components.homeassistant_ems.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_config_entry_diagnostics_redact_identifiers_and_include_site_data(
    hass: HomeAssistant,
) -> None:
    """Diagnostics include useful values/errors but omit identifying names and IDs."""
    hass.states.async_set(
        "sensor.private_grid", "-125.5", {"unit_of_measurement": "V"}
    )
    hass.states.async_set(
        "sensor.private_price",
        "2.68",
        {
            "unit_of_measurement": "SEK/kWh",
            "raw_today": [
                {
                    "start": "2026-11-24T11:00:00+01:00",
                    "end": "2026-11-24T11:15:00+01:00",
                    "value": 2.68,
                }
            ],
            "raw_tomorrow": [
                {
                    "start": "invalid",
                    "end": "2026-11-25T00:15:00+01:00",
                    "value": 2.5,
                }
            ],
        },
    )
    hass.states.async_set(
        "sensor.private_inverter", "0.85", {"unit_of_measurement": "kW"}
    )
    hass.states.async_set("sensor.private_soc", "72", {"unit_of_measurement": "%"})
    hass.states.async_set(
        "sensor.private_battery_power", "-100", {"unit_of_measurement": "W"}
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="North house",
        data={CONF_SITE_NAME: "North house"},
        options={
            CONF_SITE_ENTITIES: {
                KEY_GRID_POWER: "sensor.private_grid",
                KEY_ELECTRICITY_PRICE: "sensor.private_price",
            },
            CONF_INVERTERS: [
                {
                    CONF_INVERTER_ID: "private-inverter-id",
                    CONF_INVERTER_NAME: "Private inverter name",
                    CONF_INVERTER_POWER_ENTITY: "sensor.private_inverter",
                    CONF_BATTERIES: [
                        {
                            CONF_BATTERY_ID: "private-battery-id",
                            CONF_BATTERY_NAME: "Private battery name",
                            CONF_BATTERY_SOC_ENTITY: "sensor.private_soc",
                            CONF_BATTERY_POWER_ENTITY: "sensor.private_battery_power",
                        }
                    ],
                }
            ],
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    serialized = json.dumps(diagnostics)
    for private_value in (
        "North house",
        "Private inverter name",
        "Private battery name",
        "private-inverter-id",
        "private-battery-id",
        "sensor.private_grid",
        "sensor.private_price",
        "sensor.private_inverter",
        "sensor.private_soc",
        "sensor.private_battery_power",
    ):
        assert private_value not in serialized

    site_data = diagnostics["site_data"]
    assert site_data["measurements"][KEY_GRID_POWER]["value"] == -125.5
    assert site_data["measurements"][KEY_GRID_POWER]["unit_error"] == (
        "Expected W or kW; received 'V'"
    )
    assert site_data["inverters"][0]["ac_power"]["value"] == 0.85
    assert site_data["inverters"][0]["batteries"][0]["state_of_charge"]["value"] == 72
    assert site_data["price_today"][0]["price"] == 2.68
    assert "raw_tomorrow" in site_data["price_series_errors"]
    assert diagnostics["status"] == "loaded"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_config_entry_diagnostics_report_unloaded_entry(
    hass: HomeAssistant,
) -> None:
    """Diagnostics explicitly identify entries without runtime site data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="North house",
        data={CONF_SITE_NAME: "North house"},
    )

    assert await async_get_config_entry_diagnostics(hass, entry) == {
        "status": "not_loaded"
    }
