# Home Assistant EMS

A configurable Energy Management System for Home Assistant, intended for
distribution through the Home Assistant Marketplace.

## Status

This project is at an early development stage. The integration lets users
configure read-only site, inverter, and battery sensor mappings and publishes
mirror sensors. It does not calculate dispatch or issue control commands. Live
control is not implemented or authorized.

The initial compatibility test target is Home Assistant Core 2026.11.2. The
minimum supported version and release policy are not yet defined.

## Development

The custom integration is in `custom_components/homeassistant_ems`. Its
configuration flow records a unique site name. In the entry's **Configure**
options, map grid power, PV power, load power, electricity price, named
inverters' AC power, and zero or more named batteries per inverter with optional
SoC and power sensors. Existing inverters' battery mappings can be managed
without replacing the inverter entry.

Mapped sensors mirror numeric source values and units without conversion,
include the source entity and last-updated timestamp as attributes, and become
unavailable when their source is missing or non-numeric. Grid power is
documented as export-positive and battery power as discharge-positive; these
conventions are metadata only and values are not sign-adjusted. A stale-data
threshold is not applied: some source entities update only when their value
changes, so an unchanged value or old update timestamp alone does not mean the
reading is stale. Source semantics, unit validation, and an independent
freshness signal remain to be established.

For a Nordpool price sensor, `raw_today` and `raw_tomorrow` attributes are
mirrored when present. Their interval `start` and `end` values are preserved;
the integration does not infer interval duration from the number of prices.
A push coordinator keeps an in-memory site data model of mapped measurements,
inverters, batteries, and parsed price intervals. It updates on source state
changes without polling, preserves source units, timestamps, and sign metadata,
and does not apply age-based staleness rules. Invalid interval attributes are
reported in the model without discarding the source price reading.

The tests use `pytest-homeassistant-custom-component`. A matching Home
Assistant test runtime is not installed in this workspace yet.
