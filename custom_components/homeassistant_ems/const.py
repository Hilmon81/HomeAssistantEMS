"""Constants for Home Assistant EMS."""

DOMAIN = "homeassistant_ems"
CONF_SITE_NAME = "site_name"
CONF_SITE_ENTITIES = "site_entities"
CONF_INVERTERS = "inverters"
CONF_GRID_POWER_SIGN = "grid_power_sign"
CONF_BATTERY_POWER_SIGN = "battery_power_sign"

KEY_GRID_POWER = "grid_power"
KEY_PV_POWER = "pv_power"
KEY_LOAD_POWER = "load_power"
KEY_ELECTRICITY_PRICE = "electricity_price"
KEY_INVERTER_AC_POWER = "ac_power"
KEY_BATTERY_SOC = "state_of_charge"
KEY_BATTERY_POWER = "battery_power"

CONF_INVERTER_ID = "id"
CONF_INVERTER_NAME = "name"
CONF_INVERTER_POWER_ENTITY = "ac_power_entity_id"
CONF_BATTERIES = "batteries"
CONF_BATTERY_ID = "id"
CONF_BATTERY_NAME = "name"
CONF_BATTERY_SOC_ENTITY = "soc_entity_id"
CONF_BATTERY_POWER_ENTITY = "power_entity_id"

GRID_POWER_EXPORT_POSITIVE = "export_positive"
BATTERY_POWER_DISCHARGE_POSITIVE = "discharge_positive"

PRICE_SERIES_ATTRIBUTES = ("raw_today", "raw_tomorrow")

SITE_MEASUREMENTS = {
    KEY_GRID_POWER: "Grid power",
    KEY_PV_POWER: "PV power",
    KEY_LOAD_POWER: "Load power",
    KEY_ELECTRICITY_PRICE: "Electricity price",
}
