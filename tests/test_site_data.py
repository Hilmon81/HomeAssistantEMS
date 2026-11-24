"""Tests for the pure in-memory site data model."""

import importlib
import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_INTEGRATION_PATH = _PROJECT_ROOT / "custom_components" / "homeassistant_ems"

for _name, _path in (
    ("custom_components", _PROJECT_ROOT / "custom_components"),
    ("custom_components.homeassistant_ems", _INTEGRATION_PATH),
):
    if _name not in sys.modules:
        _package = ModuleType(_name)
        _package.__path__ = [str(_path)]
        sys.modules[_name] = _package

_site_data = importlib.import_module("custom_components.homeassistant_ems.site_data")
SiteDataStore = _site_data.SiteDataStore


def _state(
    value: str, *, unit: str | None = None, **attributes: object
) -> SimpleNamespace:
    state_attributes = dict(attributes)
    if unit is not None:
        state_attributes["unit_of_measurement"] = unit
    return SimpleNamespace(
        state=value,
        attributes=state_attributes,
        last_updated=datetime.fromisoformat("2026-11-24T11:00:00+01:00"),
    )


class SiteDataTests(unittest.TestCase):
    """Verify source values, grouping, and interval updates in the model."""

    def test_builds_mapped_site_inverter_battery_and_price_data(self) -> None:
        options = {
            "site_entities": {
                "grid_power": "sensor.grid",
                "electricity_price": "sensor.price",
            },
            "grid_power_sign": "export_positive",
            "inverters": [
                {
                    "id": "inv-1",
                    "name": "Inverter A",
                    "ac_power_entity_id": "sensor.inverter",
                    "batteries": [
                        {
                            "id": "bat-1",
                            "name": "Battery A",
                            "soc_entity_id": "sensor.soc",
                            "power_entity_id": "sensor.battery_power",
                        }
                    ],
                }
            ],
        }
        store = SiteDataStore("North house", options)
        store.update_sources(
            {
                "sensor.grid": _state("-125.5", unit="W"),
                "sensor.price": _state(
                    "0.31",
                    unit="SEK/kWh",
                    raw_today=[
                        {
                            "start": "2026-11-24T11:00:00+01:00",
                            "end": "2026-11-24T11:15:00+01:00",
                            "value": 0.31,
                        }
                    ],
                ),
                "sensor.inverter": _state("850", unit="W"),
                "sensor.soc": _state("72", unit="%"),
                "sensor.battery_power": _state("-100", unit="W"),
            }
        )

        snapshot = store.snapshot
        self.assertEqual(snapshot.site_name, "North house")
        self.assertEqual(snapshot.measurements["grid_power"].value, -125.5)
        self.assertEqual(
            snapshot.measurements["grid_power"].sign_convention, "export_positive"
        )
        self.assertEqual(snapshot.measurements["grid_power"].unit, "W")
        self.assertIsNotNone(snapshot.measurements["grid_power"].source_last_updated)
        self.assertEqual(snapshot.inverters[0].ac_power.value, 850)
        battery = snapshot.inverters[0].batteries[0]
        self.assertEqual(battery.state_of_charge.value, 72)
        self.assertEqual(battery.power.value, -100)
        self.assertEqual(battery.power.sign_convention, "discharge_positive")
        self.assertEqual(len(snapshot.price_today), 1)
        self.assertEqual(snapshot.price_today[0].duration.total_seconds(), 900)
        self.assertEqual(dict(snapshot.price_series_errors), {})

    def test_source_and_attribute_only_updates_refresh_snapshot(self) -> None:
        store = SiteDataStore(
            "North house",
            {"site_entities": {"electricity_price": "sensor.price"}},
        )
        initial = _state(
            "0.31",
            unit="SEK/kWh",
            raw_today=[
                {
                    "start": "2026-11-24T11:00:00+01:00",
                    "end": "2026-11-24T11:15:00+01:00",
                    "value": 0.31,
                }
            ],
        )
        store.update_source("sensor.price", initial)
        self.assertEqual(len(store.snapshot.price_today), 1)

        updated = _state(
            "unknown",
            unit="SEK/kWh",
            raw_today=[
                {
                    "start": "2026-11-24T11:00:00+01:00",
                    "end": "2026-11-24T11:15:00+01:00",
                    "value": 0.31,
                },
                {
                    "start": "2026-11-24T11:15:00+01:00",
                    "end": "2026-11-24T11:30:00+01:00",
                    "value": 0.29,
                },
            ],
        )
        store.update_source("sensor.price", updated)

        snapshot = store.snapshot
        self.assertFalse(snapshot.measurements["electricity_price"].available)
        self.assertEqual(len(snapshot.price_today), 2)

    def test_invalid_price_data_is_reported_without_hiding_source_reading(self) -> None:
        store = SiteDataStore(
            "North house",
            {"site_entities": {"electricity_price": "sensor.price"}},
        )
        store.update_source(
            "sensor.price",
            _state(
                "0.31",
                unit="SEK/kWh",
                raw_today=[{"start": "invalid", "end": "invalid", "value": 0.31}],
            ),
        )

        snapshot = store.snapshot
        self.assertEqual(snapshot.measurements["electricity_price"].value, 0.31)
        self.assertEqual(snapshot.price_today, ())
        self.assertIn("raw_today", snapshot.price_series_errors)


if __name__ == "__main__":
    unittest.main()
