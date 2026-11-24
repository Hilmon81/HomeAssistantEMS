"""Tests for read-only mapped sensors."""

from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.homeassistant_ems.const import (
    CONF_GRID_POWER_SIGN,
    CONF_SITE_ENTITIES,
    CONF_SITE_NAME,
    DOMAIN,
    KEY_ELECTRICITY_PRICE,
    KEY_GRID_POWER,
)


async def test_grid_sensor_mirrors_value_unit_and_unavailable_state(
    hass: HomeAssistant,
) -> None:
    """Mapped sensor preserves source units, sign, and availability."""
    source_entity_id = "sensor.site_grid"
    hass.states.async_set(source_entity_id, "-125.5", {"unit_of_measurement": "W"})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="North house",
        data={CONF_SITE_NAME: "North house"},
        options={
            CONF_SITE_ENTITIES: {KEY_GRID_POWER: source_entity_id},
            CONF_GRID_POWER_SIGN: "export_positive",
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = er.async_get(hass).async_get_entity_id(
        Platform.SENSOR, DOMAIN, f"{entry.entry_id}_{KEY_GRID_POWER}"
    )
    assert entity_id is not None
    mapped_state = hass.states.get(entity_id)
    assert mapped_state is not None
    assert mapped_state.state == "-125.5"
    assert mapped_state.attributes["unit_of_measurement"] == "W"
    assert mapped_state.attributes["sign_convention"] == "export_positive"
    assert mapped_state.attributes["source_entity_id"] == source_entity_id

    for invalid_value in ("unknown", "NaN", "inf", "-inf"):
        hass.states.async_set(source_entity_id, invalid_value)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    hass.states.async_set(source_entity_id, "-98.75", {"unit_of_measurement": "W"})
    await hass.async_block_till_done()
    recovered_state = hass.states.get(entity_id)
    assert recovered_state is not None
    assert recovered_state.state == "-98.75"
    assert recovered_state.attributes["unit_of_measurement"] == "W"

    hass.states.async_set(source_entity_id, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_price_sensor_preserves_nordpool_interval_attributes(
    hass: HomeAssistant,
) -> None:
    """Price intervals retain their source timestamps and values."""
    source_entity_id = "sensor.nordpool_price"
    raw_today = [
        {
            "start": "2026-11-24T00:00:00+01:00",
            "end": "2026-11-24T00:15:00+01:00",
            "value": 0.31,
        }
    ]
    raw_tomorrow = [
        {
            "start": "2026-11-25T00:00:00+01:00",
            "end": "2026-11-25T00:15:00+01:00",
            "value": 0.28,
        }
    ]
    hass.states.async_set(
        source_entity_id,
        "0.31",
        {
            "unit_of_measurement": "SEK/kWh",
            "raw_today": raw_today,
            "raw_tomorrow": raw_tomorrow,
        },
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="North house",
        data={CONF_SITE_NAME: "North house"},
        options={
            CONF_SITE_ENTITIES: {KEY_ELECTRICITY_PRICE: source_entity_id},
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = er.async_get(hass).async_get_entity_id(
        Platform.SENSOR, DOMAIN, f"{entry.entry_id}_{KEY_ELECTRICITY_PRICE}"
    )
    assert entity_id is not None
    mapped_state = hass.states.get(entity_id)
    assert mapped_state is not None
    assert mapped_state.state == "0.31"
    assert mapped_state.attributes["unit_of_measurement"] == "SEK/kWh"
    assert mapped_state.attributes["raw_today"] == raw_today
    assert mapped_state.attributes["raw_tomorrow"] == raw_tomorrow

    updated_raw_today = raw_today + [
        {
            "start": "2026-11-24T00:15:00+01:00",
            "end": "2026-11-24T00:30:00+01:00",
            "value": 0.29,
        }
    ]
    hass.states.async_set(
        source_entity_id,
        "0.31",
        {
            "unit_of_measurement": "SEK/kWh",
            "raw_today": updated_raw_today,
            "raw_tomorrow": raw_tomorrow,
        },
    )
    await hass.async_block_till_done()
    updated_state = hass.states.get(entity_id)
    assert updated_state is not None
    assert updated_state.attributes["raw_today"] == updated_raw_today


async def test_site_data_model_refreshes_when_price_attributes_change(
    hass: HomeAssistant,
) -> None:
    """The runtime site model follows source updates even when price is unchanged."""
    source_entity_id = "sensor.nordpool_price"
    first_interval = {
        "start": "2026-11-24T00:00:00+01:00",
        "end": "2026-11-24T00:15:00+01:00",
        "value": 0.31,
    }
    hass.states.async_set(
        source_entity_id,
        "0.31",
        {"unit_of_measurement": "SEK/kWh", "raw_today": [first_interval]},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="North house",
        data={CONF_SITE_NAME: "North house"},
        options={
            CONF_SITE_ENTITIES: {KEY_ELECTRICITY_PRICE: source_entity_id},
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime_data = entry.runtime_data
    assert runtime_data is not None
    assert len(runtime_data.site_data.snapshot.price_today) == 1
    assert runtime_data.site_data.data == runtime_data.site_data.snapshot
    assert runtime_data.site_data.update_interval is None

    second_interval = {
        "start": "2026-11-24T00:15:00+01:00",
        "end": "2026-11-24T00:30:00+01:00",
        "value": 0.29,
    }
    hass.states.async_set(
        source_entity_id,
        "0.31",
        {
            "unit_of_measurement": "SEK/kWh",
            "raw_today": [first_interval, second_interval],
        },
    )
    await hass.async_block_till_done()

    snapshot = runtime_data.site_data.snapshot
    assert [interval.price for interval in snapshot.price_today] == [0.31, 0.29]
    assert runtime_data.site_data.data == snapshot

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert getattr(entry, "runtime_data", None) is None
