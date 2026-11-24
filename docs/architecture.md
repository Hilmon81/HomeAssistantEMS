# Architecture

## Status

Proposed target only. This repository currently contains AI-team configuration and documentation, not an EMS integration implementation.

## Proposed boundaries

```text
Configured Home Assistant input entities
        |
        v
Entity-state acquisition with timestamp and availability
        |
        v
Normalization with explicit units and sign conventions
        |
        v
Site model: grid, load, PV, multiple inverters, and associated batteries
        |
        +---- Price and forecast inputs (providers and intervals UNKNOWN)
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

## Decisions still required

- How configured entities map to the site, inverters, batteries, and control targets.
- Which settable entity domains and command semantics are supported by the selected device integrations.
- Optimizer algorithm, data model, and control-cycle behavior.
- Price and forecast providers, timestamp policy, and supported interval resolutions.
- Supported Home Assistant version range and release/update policy.
- Data persistence and retention requirements.

## Marketplace constraints

The target is a custom integration published through the Home Assistant Marketplace, not an AppDaemon app. Marketplace publication requires the expected custom integration layout, a root `hacs.json` and README, a versioned manifest, published releases, and passing Marketplace and hassfest checks. See the [Marketplace custom integration guide](https://contributors.home-assistant.io/marketplace/guides/integrations/) and [validation reference](https://contributors.home-assistant.io/marketplace/reference/validation/).
