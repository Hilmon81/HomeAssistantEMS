"""Diagnostics for the Home Assistant EMS integration."""

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .price_series import PriceInterval
from .site_data import SiteData, SourceMeasurement


def _measurement_diagnostics(
    measurement: SourceMeasurement | None,
) -> dict[str, Any] | None:
    """Return a measurement without its identifying source entity ID."""
    if measurement is None:
        return None

    return {
        "available": measurement.available,
        "value": measurement.value,
        "unit": measurement.unit,
        "source_last_updated": (
            measurement.source_last_updated.isoformat()
            if measurement.source_last_updated is not None
            else None
        ),
        "sign_convention": measurement.sign_convention,
        "unit_error": measurement.unit_error,
    }


def _price_interval_diagnostics(interval: PriceInterval) -> dict[str, Any]:
    """Return a price interval using JSON-serializable timestamp strings."""
    return {
        "start": interval.start.isoformat(),
        "end": interval.end.isoformat(),
        "price": interval.price,
        "unit": interval.unit,
        "duration_seconds": interval.duration.total_seconds(),
    }


def _site_data_diagnostics(site_data: SiteData) -> dict[str, Any]:
    """Return the snapshot without site, inverter, battery, or entity identifiers."""
    return {
        "measurements": {
            key: _measurement_diagnostics(measurement)
            for key, measurement in site_data.measurements.items()
        },
        "inverters": [
            {
                "ac_power": _measurement_diagnostics(inverter.ac_power),
                "batteries": [
                    {
                        "state_of_charge": _measurement_diagnostics(
                            battery.state_of_charge
                        ),
                        "power": _measurement_diagnostics(battery.power),
                    }
                    for battery in inverter.batteries
                ],
            }
            for inverter in site_data.inverters
        ],
        "price_today": [
            _price_interval_diagnostics(interval) for interval in site_data.price_today
        ],
        "price_tomorrow": [
            _price_interval_diagnostics(interval)
            for interval in site_data.price_tomorrow
        ],
        "price_series_errors": dict(site_data.price_series_errors),
    }


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return snapshot data without configured names or entity IDs."""
    runtime_data = getattr(entry, "runtime_data", None)
    if runtime_data is None:
        return {"status": "not_loaded"}

    return {
        "status": "loaded",
        "site_data": _site_data_diagnostics(runtime_data.site_data.snapshot),
    }
