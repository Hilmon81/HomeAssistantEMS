"""Read-only sensors mirroring configured Home Assistant entities."""

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

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
    DOMAIN,
    GRID_POWER_EXPORT_POSITIVE,
    KEY_BATTERY_POWER,
    KEY_BATTERY_SOC,
    KEY_ELECTRICITY_PRICE,
    KEY_GRID_POWER,
    KEY_INVERTER_AC_POWER,
    PRICE_SERIES_ATTRIBUTES,
    SITE_MEASUREMENTS,
)
from .site_data import parse_numeric_state


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one mirror sensor for each configured source entity."""
    options = entry.options
    site_device_id = f"{entry.entry_id}_site"
    entities: list[MappedSourceSensor] = []

    for key, name in SITE_MEASUREMENTS.items():
        if source_entity_id := options.get(CONF_SITE_ENTITIES, {}).get(key):
            sign_convention = (
                options.get(CONF_GRID_POWER_SIGN, GRID_POWER_EXPORT_POSITIVE)
                if key == KEY_GRID_POWER
                else None
            )
            entities.append(
                MappedSourceSensor(
                    source_entity_id=source_entity_id,
                    unique_id=f"{entry.entry_id}_{key}",
                    name=name,
                    measurement_key=key,
                    device_info=DeviceInfo(
                        identifiers={(DOMAIN, site_device_id)},
                        name=entry.title,
                    ),
                    sign_convention=sign_convention,
                )
            )

    for inverter in options.get(CONF_INVERTERS, []):
        inverter_id = inverter[CONF_INVERTER_ID]
        inverter_device_id = f"{entry.entry_id}_inverter_{inverter_id}"
        entities.append(
            MappedSourceSensor(
                source_entity_id=inverter[CONF_INVERTER_POWER_ENTITY],
                unique_id=f"{entry.entry_id}_inverter_{inverter_id}_{KEY_INVERTER_AC_POWER}",
                name="AC power",
                measurement_key=KEY_INVERTER_AC_POWER,
                device_info=DeviceInfo(
                    identifiers={(DOMAIN, inverter_device_id)},
                    name=inverter[CONF_INVERTER_NAME],
                ),
            )
        )

        for battery in inverter.get(CONF_BATTERIES, []):
            battery_id = battery[CONF_BATTERY_ID]
            battery_device_id = f"{entry.entry_id}_battery_{battery_id}"
            battery_device = DeviceInfo(
                identifiers={(DOMAIN, battery_device_id)},
                name=battery[CONF_BATTERY_NAME],
            )
            if source_entity_id := battery.get(CONF_BATTERY_SOC_ENTITY):
                entities.append(
                    MappedSourceSensor(
                        source_entity_id=source_entity_id,
                        unique_id=(
                            f"{entry.entry_id}_battery_{battery_id}_{KEY_BATTERY_SOC}"
                        ),
                        name="State of charge",
                        measurement_key=KEY_BATTERY_SOC,
                        device_info=battery_device,
                    )
                )
            if source_entity_id := battery.get(CONF_BATTERY_POWER_ENTITY):
                entities.append(
                    MappedSourceSensor(
                        source_entity_id=source_entity_id,
                        unique_id=(
                            f"{entry.entry_id}_battery_{battery_id}_{KEY_BATTERY_POWER}"
                        ),
                        name="Battery power",
                        measurement_key=KEY_BATTERY_POWER,
                        device_info=battery_device,
                        sign_convention=options.get(
                            CONF_BATTERY_POWER_SIGN,
                            BATTERY_POWER_DISCHARGE_POSITIVE,
                        ),
                    )
                )

    async_add_entities(entities)


class MappedSourceSensor(SensorEntity):
    """Expose a numeric source value without changing its unit or sign."""

    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset(PRICE_SERIES_ATTRIBUTES)

    def __init__(
        self,
        *,
        source_entity_id: str,
        unique_id: str,
        name: str,
        measurement_key: str,
        device_info: DeviceInfo,
        sign_convention: str | None = None,
    ) -> None:
        """Initialize the source mapping."""
        self.source_entity_id = source_entity_id
        self.measurement_key = measurement_key
        self.sign_convention = sign_convention
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_device_info = device_info

    @property
    def native_value(self) -> float | None:
        """Return the numeric source value, or None for invalid source states."""
        state = self._source_state
        return parse_numeric_state(state.state) if state is not None else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit currently reported by the source entity."""
        state = self._source_state
        unit = state.attributes.get("unit_of_measurement") if state else None
        return unit if isinstance(unit, str) else None

    @property
    def available(self) -> bool:
        """Mark missing, unavailable, and non-numeric source states unavailable."""
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose provenance and the source timestamp for observability."""
        state = self._source_state
        attributes: dict[str, Any] = {
            "measurement": self.measurement_key,
            "source_entity_id": self.source_entity_id,
        }
        if state is not None:
            attributes["source_last_updated"] = state.last_updated.isoformat()
            if self.measurement_key == KEY_ELECTRICITY_PRICE:
                attributes.update(
                    {
                        key: state.attributes[key]
                        for key in PRICE_SERIES_ATTRIBUTES
                        if key in state.attributes
                    }
                )
        if self.sign_convention is not None:
            attributes["sign_convention"] = self.sign_convention
        return attributes

    @property
    def _source_state(self) -> State | None:
        """Read the current source state without retaining stale values."""
        return self.hass.states.get(self.source_entity_id)

    async def async_added_to_hass(self) -> None:
        """Subscribe to source changes after registration."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.source_entity_id], self._handle_state_change
            )
        )

    @callback
    def _handle_state_change(self, _event: Event) -> None:
        """Refresh this mirror when its source entity changes."""
        self.async_write_ha_state()
