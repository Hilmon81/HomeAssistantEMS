"""Config flow for Home Assistant EMS."""

from copy import deepcopy
from typing import Any
from uuid import uuid4

import probatio
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    BATTERY_POWER_DISCHARGE_POSITIVE,
    CONF_BATTERIES,
    CONF_BATTERY_ID,
    CONF_BATTERY_NAME,
    CONF_BATTERY_POWER_ENTITY,
    CONF_BATTERY_POWER_SIGN,
    CONF_BATTERY_SOC_ENTITY,
    CONF_GRID_POWER_SIGN,
    CONF_INVERTER_ID,
    CONF_INVERTER_NAME,
    CONF_INVERTER_POWER_ENTITY,
    CONF_INVERTERS,
    CONF_SITE_ENTITIES,
    CONF_SITE_NAME,
    DOMAIN,
    GRID_POWER_EXPORT_POSITIVE,
    SITE_MEASUREMENTS,
)


class HomeAssistantEMSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Home Assistant EMS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create a site config entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            site_name = user_input[CONF_SITE_NAME].strip()

            if not site_name:
                errors["base"] = "invalid_site_name"
            elif any(
                entry.data.get(CONF_SITE_NAME, "").casefold() == site_name.casefold()
                for entry in self.hass.config_entries.async_entries(DOMAIN)
            ):
                errors["base"] = "already_configured"
            else:
                return self.async_create_entry(
                    title=site_name,
                    data={CONF_SITE_NAME: site_name},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_SITE_NAME): selector.TextSelector(),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return the site mapping options flow."""
        return HomeAssistantEMSOptionsFlow()


class HomeAssistantEMSOptionsFlow(OptionsFlowWithReload):
    """Manage a site's read-only entity mappings."""

    def __init__(self) -> None:
        """Initialize the options flow state."""
        self._site_entities: dict[str, str] = {}
        self._inverters: list[dict[str, Any]] = []
        self._grid_power_sign = GRID_POWER_EXPORT_POSITIVE
        self._battery_power_sign = BATTERY_POWER_DISCHARGE_POSITIVE
        self._pending_inverter: dict[str, Any] | None = None
        self._active_inverter: dict[str, Any] | None = None
        self._initialized = False

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the mapping menu."""
        if not self._initialized:
            self._site_entities = dict(
                self.config_entry.options.get(CONF_SITE_ENTITIES, {})
            )
            self._inverters = deepcopy(
                self.config_entry.options.get(CONF_INVERTERS, [])
            )
            self._grid_power_sign = self.config_entry.options.get(
                CONF_GRID_POWER_SIGN, GRID_POWER_EXPORT_POSITIVE
            )
            self._battery_power_sign = self.config_entry.options.get(
                CONF_BATTERY_POWER_SIGN, BATTERY_POWER_DISCHARGE_POSITIVE
            )
            self._initialized = True
        menu_options = ["site_mapping", "add_inverter"]
        if self._inverters:
            menu_options.extend(["manage_inverter", "remove_inverter"])
        menu_options.append("finish")
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    async def async_step_site_mapping(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the site's read-only measurement entities."""
        if user_input is not None:
            self._site_entities = {
                key: entity_id
                for key, entity_id in user_input.items()
                if entity_id
            }
            return await self.async_step_init()

        schema: dict[Any, Any] = {}
        for key in SITE_MEASUREMENTS:
            schema[probatio.Optional(key)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
        return self.async_show_form(
            step_id="site_mapping",
            data_schema=self.add_suggested_values_to_schema(
                probatio.Schema(schema), self._site_entities
            ),
        )

    async def async_step_add_inverter(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a named inverter and its AC power measurement."""
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_INVERTER_NAME].strip()
            if not name:
                errors["base"] = "invalid_name"
            elif any(
                inverter[CONF_INVERTER_NAME].casefold() == name.casefold()
                for inverter in self._inverters
            ):
                errors["base"] = "duplicate_inverter"
            else:
                self._pending_inverter = {
                    CONF_INVERTER_ID: uuid4().hex,
                    CONF_INVERTER_NAME: name,
                    CONF_INVERTER_POWER_ENTITY: user_input[
                        CONF_INVERTER_POWER_ENTITY
                    ],
                    CONF_BATTERIES: [],
                }
                self._active_inverter = self._pending_inverter
                return await self.async_step_battery_menu()

        return self.async_show_form(
            step_id="add_inverter",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_INVERTER_NAME): selector.TextSelector(),
                    probatio.Required(
                        CONF_INVERTER_POWER_ENTITY
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_manage_inverter(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select an existing inverter to manage its batteries."""
        if user_input is not None:
            inverter_id = user_input[CONF_INVERTER_ID]
            self._active_inverter = next(
                inverter
                for inverter in self._inverters
                if inverter[CONF_INVERTER_ID] == inverter_id
            )
            return await self.async_step_battery_menu()

        return self.async_show_form(
            step_id="manage_inverter",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_INVERTER_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": inverter[CONF_INVERTER_ID],
                                    "label": inverter[CONF_INVERTER_NAME],
                                }
                                for inverter in self._inverters
                            ]
                        )
                    )
                }
            ),
        )

    async def async_step_battery_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose how to manage batteries for the selected inverter."""
        assert self._active_inverter is not None
        menu_options = ["add_battery"]
        if self._active_inverter[CONF_BATTERIES]:
            menu_options.append("remove_battery")
        menu_options.append("finish_inverter")
        return self.async_show_menu(
            step_id="battery_menu",
            menu_options=menu_options,
        )

    async def async_step_add_battery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a named battery and its available read-only measurements."""
        assert self._active_inverter is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_BATTERY_NAME].strip()
            if not name:
                errors["base"] = "invalid_name"
            elif any(
                battery[CONF_BATTERY_NAME].casefold() == name.casefold()
                for battery in self._active_inverter[CONF_BATTERIES]
            ):
                errors["base"] = "duplicate_battery"
            elif not (
                user_input.get(CONF_BATTERY_SOC_ENTITY)
                or user_input.get(CONF_BATTERY_POWER_ENTITY)
            ):
                errors["base"] = "battery_measurement_required"
            else:
                battery = {
                    CONF_BATTERY_ID: uuid4().hex,
                    CONF_BATTERY_NAME: name,
                }
                if soc_entity_id := user_input.get(CONF_BATTERY_SOC_ENTITY):
                    battery[CONF_BATTERY_SOC_ENTITY] = soc_entity_id
                if power_entity_id := user_input.get(CONF_BATTERY_POWER_ENTITY):
                    battery[CONF_BATTERY_POWER_ENTITY] = power_entity_id
                self._active_inverter[CONF_BATTERIES].append(battery)
                return await self.async_step_battery_menu()

        schema: dict[Any, Any] = {
            probatio.Required(CONF_BATTERY_NAME): selector.TextSelector()
        }
        for key in (CONF_BATTERY_SOC_ENTITY, CONF_BATTERY_POWER_ENTITY):
            schema[probatio.Optional(key)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
        return self.async_show_form(
            step_id="add_battery",
            data_schema=probatio.Schema(schema),
            errors=errors,
        )

    async def async_step_finish_inverter(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Finish managing batteries and return to the mapping menu."""
        if self._pending_inverter is not None:
            self._inverters.append(self._pending_inverter)
        self._pending_inverter = None
        self._active_inverter = None
        return await self.async_step_init()

    async def async_step_remove_battery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Remove a battery mapping from the selected inverter."""
        assert self._active_inverter is not None
        batteries = self._active_inverter[CONF_BATTERIES]
        if user_input is not None:
            battery_id = user_input[CONF_BATTERY_ID]
            self._active_inverter[CONF_BATTERIES] = [
                battery
                for battery in batteries
                if battery[CONF_BATTERY_ID] != battery_id
            ]
            return await self.async_step_battery_menu()

        return self.async_show_form(
            step_id="remove_battery",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_BATTERY_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": battery[CONF_BATTERY_ID],
                                    "label": battery[CONF_BATTERY_NAME],
                                }
                                for battery in batteries
                            ]
                        )
                    )
                }
            ),
        )

    async def async_step_remove_inverter(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Remove an inverter and its associated battery mappings."""
        if user_input is not None:
            inverter_id = user_input[CONF_INVERTER_ID]
            self._inverters = [
                inverter
                for inverter in self._inverters
                if inverter[CONF_INVERTER_ID] != inverter_id
            ]
            return await self.async_step_init()

        return self.async_show_form(
            step_id="remove_inverter",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_INVERTER_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": inverter[CONF_INVERTER_ID],
                                    "label": inverter[CONF_INVERTER_NAME],
                                }
                                for inverter in self._inverters
                            ]
                        )
                    )
                }
            ),
        )

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Save the mappings and confirmed power sign conventions."""
        options = {
            CONF_SITE_ENTITIES: self._site_entities,
            CONF_INVERTERS: self._inverters,
            CONF_GRID_POWER_SIGN: self._grid_power_sign,
            CONF_BATTERY_POWER_SIGN: self._battery_power_sign,
        }
        return self.async_create_entry(data=options)
