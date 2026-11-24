# Architecture

## Status

Implementation has started. The integration creates a named site entry and
supports configurable, read-only entity mappings for site measurements,
inverters, and associated batteries. It mirrors numeric values and source units
as Home Assistant sensors. It does not calculate dispatch or write to devices.

## Proposed boundaries

```text
Configured Home Assistant input entities
        |
        v
Read-only sensor mirrors and a push coordinator with an in-memory site model
        |
        v
Explicit sign-convention metadata (no normalization or conversion yet)
        |
        v
Site model: grid, load, PV, multiple inverters, and associated batteries
        |
        +---- Nordpool price series (forecast input UNKNOWN)
        |
        v
EMS planning and control policy (runs inside the Home Assistant integration)
        |
        v
Safety validation: freshness, units, configured limits, and armed state
        |
        v
Configured settable Home Assistant entities (domains and command semantics UNKNOWN)
        |
        v
Applied state and independent feedback
        |
        v
Home Assistant diagnostics and alerts
```

Home Assistant remains the I/O layer. Do not create parallel device or Modbus connections when an existing Home Assistant integration owns the device connection.

Control is in the first-milestone scope, but live physical output remains disabled until its target, semantics, constraints, feedback, failure behavior, and rollback are verified. Test planning and command handling with simulation and fakes first. Require explicit human approval before a bounded live test. The controller must not bypass safety validation or the serialized control path.

## Confirmed decisions

- The Home Assistant domain is `homeassistant_ems`.
- The initial mapping scope is site measurements plus named inverters and their associated batteries.
- Site measurements include grid power, PV power, load power, and electricity price.
- Each inverter has an AC power sensor and can be associated with zero or more named batteries.
- Battery mappings can include state of charge, battery power, or both.
- Grid power is export-positive; battery power is discharge-positive. The integration records these conventions but does not change sensor values.
- Mapped sensor values and units are mirrored from their source entities; no conversion is performed.
- Source update timestamps are informational only. Some source entities update only when their value changes, so an unchanged value or old `last_updated` timestamp alone must not mark a reading stale or unavailable.
- A selected Nordpool price sensor's `raw_today` and `raw_tomorrow` attributes are mirrored when present. Each interval's source `start`, `end`, and `value` are preserved; interval duration is not inferred from list length.
- A push coordinator keeps an in-memory site data model of mapped readings and parsed Nordpool intervals. It refreshes on mapped source state changes without polling, keeps source values, units, timestamps, and sign metadata, and does not apply age-based staleness rules.
- Future integration consumers can subscribe through `entry.runtime_data.site_data` and read the current snapshot from the coordinator's `data`.
- The owner reports Nordpool prices in SEK/kWh at 15-minute intervals. The price sensor is selected in the integration options; the installed Nordpool version's exact attributes still need verification.

## Decisions still required

- Source measurement semantics, expected units, unit validation, and a reliable freshness signal (such as a source-provided heartbeat) before stale-data handling is introduced.
- Control-target entities, semantics, feedback, and rollback requirements.
- Which settable entity domains and command semantics are supported by the selected device integrations.
- Optimizer algorithm, data model, and control-cycle behavior.
- Forecast provider and timestamp policy; validate real Nordpool interval data before calculations.
- Supported Home Assistant version range and release/update policy.
- Data persistence and retention requirements.

## Marketplace constraints

The target is a custom integration published through the Home Assistant Marketplace, not an AppDaemon app. Marketplace publication requires the expected custom integration layout, a root `hacs.json` and README, a versioned manifest, published releases, and passing Marketplace and hassfest checks. See the [Marketplace custom integration guide](https://contributors.home-assistant.io/marketplace/guides/integrations/) and [validation reference](https://contributors.home-assistant.io/marketplace/reference/validation/).
