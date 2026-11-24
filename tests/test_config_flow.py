"""Tests for the Home Assistant EMS config flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.homeassistant_ems.const import (
    CONF_BATTERIES,
    CONF_BATTERY_ID,
    CONF_BATTERY_NAME,
    CONF_BATTERY_POWER_ENTITY,
    CONF_INVERTER_ID,
    CONF_INVERTER_NAME,
    CONF_INVERTER_POWER_ENTITY,
    CONF_INVERTERS,
    CONF_SITE_NAME,
    DOMAIN,
)


async def test_user_flow_creates_site_entry(hass: HomeAssistant) -> None:
    """A valid site name creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_SITE_NAME: "North house"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "North house"
    assert result["data"] == {CONF_SITE_NAME: "North house"}


async def test_user_flow_rejects_duplicate_site_name(hass: HomeAssistant) -> None:
    """Site names are unique within this integration."""
    MockConfigEntry(
        domain=DOMAIN,
        title="North house",
        data={CONF_SITE_NAME: "North house"},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_SITE_NAME: "NORTH HOUSE"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "already_configured"}


async def test_user_flow_rejects_blank_site_name(hass: HomeAssistant) -> None:
    """A blank site name does not create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_SITE_NAME: "  "}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_site_name"}


async def test_options_flow_maps_site_and_multiple_batteries(hass: HomeAssistant) -> None:
    """Mappings retain the confirmed signs and battery-to-inverter grouping."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="North house",
        data={CONF_SITE_NAME: "North house"},
    )
    entry.add_to_hass(hass)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow_id = flow["flow_id"]

    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "site_mapping"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id,
        user_input={
            "grid_power": "sensor.grid_power",
            "pv_power": "sensor.pv_power",
            "load_power": "sensor.load_power",
            "electricity_price": "sensor.electricity_price",
        },
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "add_inverter"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id,
        user_input={
            "name": "Inverter A",
            "ac_power_entity_id": "sensor.inverter_a_power",
        },
    )

    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "add_battery"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"name": "Battery A"}
    )
    assert flow["type"] is FlowResultType.FORM
    assert flow["errors"] == {"base": "battery_measurement_required"}
    flow = await hass.config_entries.options.async_configure(
        flow_id,
        user_input={
            "name": "Battery A",
            "soc_entity_id": "sensor.battery_a_soc",
            "power_entity_id": "sensor.battery_a_power",
        },
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "add_battery"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id,
        user_input={
            "name": "Battery B",
            "soc_entity_id": "sensor.battery_b_soc",
            "power_entity_id": "sensor.battery_b_power",
        },
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "finish_inverter"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "finish"}
    )

    assert flow["type"] is FlowResultType.CREATE_ENTRY
    assert flow["data"]["site_entities"] == {
        "grid_power": "sensor.grid_power",
        "pv_power": "sensor.pv_power",
        "load_power": "sensor.load_power",
        "electricity_price": "sensor.electricity_price",
    }
    assert flow["data"]["grid_power_sign"] == "export_positive"
    assert flow["data"]["battery_power_sign"] == "discharge_positive"
    inverter = flow["data"]["inverters"][0]
    assert inverter["name"] == "Inverter A"
    assert inverter["ac_power_entity_id"] == "sensor.inverter_a_power"
    assert [battery["name"] for battery in inverter["batteries"]] == [
        "Battery A",
        "Battery B",
    ]


async def test_options_flow_removes_battery_from_existing_inverter(
    hass: HomeAssistant,
) -> None:
    """A battery can be removed without replacing its inverter."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="North house",
        data={CONF_SITE_NAME: "North house"},
        options={
            CONF_INVERTERS: [
                {
                    CONF_INVERTER_ID: "inverter-a",
                    CONF_INVERTER_NAME: "Inverter A",
                    CONF_INVERTER_POWER_ENTITY: "sensor.inverter_a_power",
                    CONF_BATTERIES: [
                        {
                            CONF_BATTERY_ID: "battery-a",
                            CONF_BATTERY_NAME: "Battery A",
                            CONF_BATTERY_POWER_ENTITY: "sensor.battery_a_power",
                        }
                    ],
                }
            ]
        },
    )
    entry.add_to_hass(hass)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow_id = flow["flow_id"]

    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "manage_inverter"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={CONF_INVERTER_ID: "inverter-a"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "remove_battery"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={CONF_BATTERY_ID: "battery-a"}
    )
    assert entry.options[CONF_INVERTERS][0][CONF_BATTERIES][0][CONF_BATTERY_ID] == (
        "battery-a"
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "finish_inverter"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow_id, user_input={"next_step_id": "finish"}
    )

    assert flow["type"] is FlowResultType.CREATE_ENTRY
    inverter = flow["data"][CONF_INVERTERS][0]
    assert inverter[CONF_INVERTER_ID] == "inverter-a"
    assert inverter[CONF_BATTERIES] == []
