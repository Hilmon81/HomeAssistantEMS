"""Parse explicit price intervals without inferring durations from list size."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite


@dataclass(frozen=True)
class PriceInterval:
    """A source price and its explicitly reported time bounds and unit."""

    start: datetime
    end: datetime
    price: float
    unit: str

    def __post_init__(self) -> None:
        """Validate timestamps, interval bounds, value, and unit."""
        for field_name, timestamp in (("start", self.start), ("end", self.end)):
            if not isinstance(timestamp, datetime):
                raise TypeError(f"{field_name} must be a datetime")
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError(f"{field_name} timestamp must include a timezone")
        if self.end.astimezone(timezone.utc) <= self.start.astimezone(timezone.utc):
            raise ValueError("interval end must be after interval start")
        if isinstance(self.price, bool) or not isinstance(self.price, (int, float)):
            raise TypeError("price must be numeric")
        if not isfinite(self.price):
            raise ValueError("price must be finite")
        if not isinstance(self.unit, str):
            raise TypeError("price unit must be a string")
        if not self.unit.strip():
            raise ValueError("price unit must be non-empty")

    @property
    def duration(self) -> timedelta:
        """Return elapsed duration using absolute timestamps across DST changes."""
        return self.end.astimezone(timezone.utc) - self.start.astimezone(timezone.utc)


def parse_price_series(
    raw_intervals: Sequence[object], *, unit: str
) -> tuple[PriceInterval, ...]:
    """Parse Nordpool-style records with explicit start, end, and value fields."""
    if not isinstance(raw_intervals, Sequence) or isinstance(
        raw_intervals, (str, bytes, bytearray)
    ):
        raise TypeError("price series must be a sequence of interval records")
    if not isinstance(unit, str):
        raise TypeError("price unit must be a string")
    if not unit.strip():
        raise ValueError("price unit must be non-empty")

    intervals: list[PriceInterval] = []
    for index, record in enumerate(raw_intervals):
        if not isinstance(record, Mapping):
            raise TypeError(f"interval {index} must be a mapping")

        start = _parse_timestamp(record.get("start"), index, "start")
        end = _parse_timestamp(record.get("end"), index, "end")
        raw_price = record.get("value")
        if isinstance(raw_price, bool) or not isinstance(raw_price, (int, float)):
            raise TypeError(f"interval {index} value must be numeric")

        try:
            price = float(raw_price)
        except OverflowError as err:
            raise ValueError(f"interval {index} value is out of range") from err

        try:
            intervals.append(PriceInterval(start, end, price, unit))
        except ValueError as err:
            raise ValueError(f"invalid interval {index}: {err}") from err

    return tuple(intervals)


def _parse_timestamp(value: object, index: int, field_name: str) -> datetime:
    """Parse a timezone-aware datetime value from Home Assistant attributes."""
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, str):
        try:
            timestamp = datetime.fromisoformat(value)
        except ValueError as err:
            raise ValueError(
                f"interval {index} {field_name} timestamp is invalid"
            ) from err
    elif value is None:
        raise ValueError(f"interval {index} {field_name} timestamp is missing")
    else:
        raise TypeError(
            f"interval {index} {field_name} timestamp must be a string or datetime"
        )

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(
            f"interval {index} {field_name} timestamp must include a timezone"
        )
    return timestamp
