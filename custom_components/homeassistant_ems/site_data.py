"""Read-only, in-memory site data model."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from types import MappingProxyType
from typing import Any, Protocol

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
    GRID_POWER_EXPORT_POSITIVE,
    KEY_ELECTRICITY_PRICE,
    KEY_GRID_POWER,
    PRICE_SERIES_ATTRIBUTES,
)
from .price_series import PriceInterval, parse_price_series


class SourceState(Protocol):
    """The Home Assistant state fields used by the pure site data model."""

    state: str
    attributes: Mapping[str, Any]
    last_updated: datetime


@dataclass(frozen=True)
class SourceMeasurement:
    """A read-only numeric reading with its source provenance."""

    source_entity_id: str
    value: float | None
    unit: str | None
    source_last_updated: datetime | None
    sign_convention: str | None = None

    @property
    def available(self) -> bool:
        """Return whether the source currently contains a finite numeric value."""
        return self.value is not None


@dataclass(frozen=True)
class BatteryData:
    """Configured measurements for one battery."""

    identifier: str
    name: str
    state_of_charge: SourceMeasurement | None
    power: SourceMeasurement | None


@dataclass(frozen=True)
class InverterData:
    """Configured measurements for one inverter and its associated batteries."""

    identifier: str
    name: str
    ac_power: SourceMeasurement
    batteries: tuple[BatteryData, ...]


@dataclass(frozen=True)
class SiteData:
    """Latest mapped site readings and explicitly bounded price intervals."""

    site_name: str
    measurements: Mapping[str, SourceMeasurement]
    inverters: tuple[InverterData, ...]
    price_today: tuple[PriceInterval, ...]
    price_tomorrow: tuple[PriceInterval, ...]
    price_series_errors: Mapping[str, str]


def parse_numeric_state(value: str) -> float | None:
    """Return a finite numeric state, or None when it is not usable."""
    try:
        parsed_value = float(value)
    except ValueError:
        return None
    return parsed_value if isfinite(parsed_value) else None


def _measurement(
    source_entity_id: str,
    state: SourceState | None,
    sign_convention: str | None = None,
) -> SourceMeasurement:
    """Build a numeric reading without converting its value, unit, or sign."""
    value: float | None = None
    unit: str | None = None
    last_updated: datetime | None = None
    if state is not None:
        value = parse_numeric_state(state.state)
        source_unit = state.attributes.get("unit_of_measurement")
        if isinstance(source_unit, str):
            unit = source_unit
        last_updated = state.last_updated

    return SourceMeasurement(
        source_entity_id=source_entity_id,
        value=value,
        unit=unit,
        source_last_updated=last_updated,
        sign_convention=sign_convention,
    )


def _configured_source_ids(options: Mapping[str, Any]) -> tuple[str, ...]:
    """Return unique source entity IDs in their configuration order."""
    entity_ids: list[str] = []
    entity_ids.extend(
        source_id
        for source_id in options.get(CONF_SITE_ENTITIES, {}).values()
        if source_id
    )
    for inverter in options.get(CONF_INVERTERS, []):
        entity_ids.append(inverter[CONF_INVERTER_POWER_ENTITY])
        for battery in inverter.get(CONF_BATTERIES, []):
            for key in (CONF_BATTERY_SOC_ENTITY, CONF_BATTERY_POWER_ENTITY):
                if source_id := battery.get(key):
                    entity_ids.append(source_id)
    return tuple(dict.fromkeys(entity_ids))


def build_site_data(
    site_name: str,
    options: Mapping[str, Any],
    states: Mapping[str, SourceState | None],
) -> SiteData:
    """Create an immutable snapshot from configured mappings and source states."""
    measurements: dict[str, SourceMeasurement] = {}
    site_entities = options.get(CONF_SITE_ENTITIES, {})
    grid_sign = options.get(CONF_GRID_POWER_SIGN, GRID_POWER_EXPORT_POSITIVE)

    for key, source_entity_id in site_entities.items():
        if source_entity_id:
            sign = grid_sign if key == KEY_GRID_POWER else None
            measurements[key] = _measurement(
                source_entity_id, states.get(source_entity_id), sign
            )

    price_today: tuple[PriceInterval, ...] = ()
    price_tomorrow: tuple[PriceInterval, ...] = ()
    price_errors: dict[str, str] = {}
    price_entity_id = site_entities.get(KEY_ELECTRICITY_PRICE)
    price_state = states.get(price_entity_id) if price_entity_id else None
    if price_state is not None:
        for attribute_name in PRICE_SERIES_ATTRIBUTES:
            if attribute_name not in price_state.attributes:
                continue
            try:
                intervals = parse_price_series(
                    price_state.attributes[attribute_name],
                    unit=measurements[KEY_ELECTRICITY_PRICE].unit or "",
                )
            except (TypeError, ValueError) as err:
                price_errors[attribute_name] = str(err)
                continue
            if attribute_name == "raw_today":
                price_today = intervals
            else:
                price_tomorrow = intervals

    inverters: list[InverterData] = []
    battery_sign = options.get(
        CONF_BATTERY_POWER_SIGN, BATTERY_POWER_DISCHARGE_POSITIVE
    )
    for inverter in options.get(CONF_INVERTERS, []):
        inverter_power_id = inverter[CONF_INVERTER_POWER_ENTITY]
        batteries: list[BatteryData] = []
        for battery in inverter.get(CONF_BATTERIES, []):
            soc_entity_id = battery.get(CONF_BATTERY_SOC_ENTITY)
            power_entity_id = battery.get(CONF_BATTERY_POWER_ENTITY)
            batteries.append(
                BatteryData(
                    identifier=battery[CONF_BATTERY_ID],
                    name=battery[CONF_BATTERY_NAME],
                    state_of_charge=(
                        _measurement(soc_entity_id, states.get(soc_entity_id))
                        if soc_entity_id
                        else None
                    ),
                    power=(
                        _measurement(
                            power_entity_id,
                            states.get(power_entity_id),
                            battery_sign,
                        )
                        if power_entity_id
                        else None
                    ),
                )
            )
        inverters.append(
            InverterData(
                identifier=inverter[CONF_INVERTER_ID],
                name=inverter[CONF_INVERTER_NAME],
                ac_power=_measurement(
                    inverter_power_id, states.get(inverter_power_id)
                ),
                batteries=tuple(batteries),
            )
        )

    return SiteData(
        site_name=site_name,
        measurements=MappingProxyType(measurements),
        inverters=tuple(inverters),
        price_today=price_today,
        price_tomorrow=price_tomorrow,
        price_series_errors=MappingProxyType(price_errors),
    )


class SiteDataStore:
    """Keep the current site snapshot synchronized with configured source states."""

    def __init__(self, site_name: str, options: Mapping[str, Any]) -> None:
        """Initialize a store for one config entry."""
        self._site_name = site_name
        self._options = deepcopy(dict(options))
        self._source_entity_ids = _configured_source_ids(self._options)
        self._states: dict[str, SourceState | None] = {}
        self._snapshot = build_site_data(site_name, self._options, self._states)

    @property
    def source_entity_ids(self) -> tuple[str, ...]:
        """Return the entity IDs this site data store observes."""
        return self._source_entity_ids

    @property
    def snapshot(self) -> SiteData:
        """Return the latest read-only site snapshot."""
        return self._snapshot

    def update_sources(self, states: Mapping[str, SourceState | None]) -> None:
        """Replace current mapped source states and rebuild the snapshot."""
        self._states = {
            entity_id: states.get(entity_id) for entity_id in self._source_entity_ids
        }
        self._snapshot = build_site_data(self._site_name, self._options, self._states)

    def update_source(
        self, source_entity_id: str, state: SourceState | None
    ) -> None:
        """Update one mapped source and rebuild the snapshot."""
        if source_entity_id not in self._source_entity_ids:
            raise KeyError(f"unmapped source entity: {source_entity_id}")
        self._states[source_entity_id] = state
        self._snapshot = build_site_data(self._site_name, self._options, self._states)
