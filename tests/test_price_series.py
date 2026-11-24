"""Unit tests for parsing price intervals without Home Assistant."""

import sys
import unittest
from datetime import datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "homeassistant_ems"
    / "price_series.py"
)
_MODULE_SPEC = spec_from_file_location("ems_price_series", _MODULE_PATH)
if _MODULE_SPEC is None or _MODULE_SPEC.loader is None:
    raise ImportError(f"Cannot load price-series module from {_MODULE_PATH}")
_MODULE = module_from_spec(_MODULE_SPEC)
sys.modules[_MODULE_SPEC.name] = _MODULE
_MODULE_SPEC.loader.exec_module(_MODULE)
parse_price_series = _MODULE.parse_price_series


class PriceSeriesTests(unittest.TestCase):
    """Test timestamp-preserving price interval parsing."""

    def test_explicit_bounds_support_15_minute_and_hourly_intervals(self) -> None:
        """Duration comes from source bounds, not the number of records."""
        intervals = parse_price_series(
            [
                {
                    "start": "2026-11-24T00:00:00+01:00",
                    "end": "2026-11-24T00:15:00+01:00",
                    "value": 0.31,
                },
                {
                    "start": "2026-11-24T01:00:00+01:00",
                    "end": "2026-11-24T02:00:00+01:00",
                    "value": 0.28,
                },
            ],
            unit="SEK/kWh",
        )

        self.assertEqual(
            [interval.duration for interval in intervals],
            [timedelta(minutes=15), timedelta(hours=1)],
        )
        self.assertEqual(intervals[0].unit, "SEK/kWh")
        self.assertEqual(intervals[0].price, 0.31)

    def test_dst_fallback_uses_elapsed_time_and_preserves_source_timestamps(
        self,
    ) -> None:
        """Repeated local clock times remain distinct by their UTC offsets."""
        start = datetime.fromisoformat("2026-10-25T02:45:00+02:00")
        end = datetime.fromisoformat("2026-10-25T02:00:00+01:00")

        (interval,) = parse_price_series(
            [{"start": start, "end": end, "value": 0.42}],
            unit="SEK/kWh",
        )

        self.assertEqual(interval.duration, timedelta(minutes=15))
        self.assertEqual(interval.start, start)
        self.assertEqual(interval.end, end)

    def test_empty_series_is_valid(self) -> None:
        """An unpublished or absent future series can be represented as empty."""
        self.assertEqual(parse_price_series([], unit="SEK/kWh"), ())

    def test_rejects_naive_timestamp(self) -> None:
        """A timestamp without timezone information is ambiguous."""
        with self.assertRaisesRegex(ValueError, "must include a timezone"):
            parse_price_series(
                [
                    {
                        "start": "2026-11-24T00:00:00",
                        "end": "2026-11-24T00:15:00+01:00",
                        "value": 0.31,
                    }
                ],
                unit="SEK/kWh",
            )

    def test_rejects_non_finite_price(self) -> None:
        """NaN and infinite prices cannot enter the normalized model."""
        with self.assertRaisesRegex(ValueError, "price must be finite"):
            parse_price_series(
                [
                    {
                        "start": "2026-11-24T00:00:00+01:00",
                        "end": "2026-11-24T00:15:00+01:00",
                        "value": float("nan"),
                    }
                ],
                unit="SEK/kWh",
            )

    def test_rejects_non_positive_duration(self) -> None:
        """End must follow start in absolute time."""
        with self.assertRaisesRegex(ValueError, "interval end must be after"):
            parse_price_series(
                [
                    {
                        "start": "2026-11-24T00:15:00+01:00",
                        "end": "2026-11-24T00:00:00+01:00",
                        "value": 0.31,
                    }
                ],
                unit="SEK/kWh",
            )


if __name__ == "__main__":
    unittest.main()
