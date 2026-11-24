---
name: diagnose-ems
description: Diagnose an EMS issue layer by layer without unsafe device writes.
disable-model-invocation: true
---
Diagnose the EMS issue in read-only mode.

1. State observed behavior, expected behavior and time window.
2. Verify input freshness, timestamps, units and sign conventions.
3. Check forecasts, price interval length, SoC and constraints.
4. Check optimizer feasibility and desired versus applied versus feedback.
5. Check connection ownership, retries, watchdog and fallback.
6. Produce one bounded next test at a time, evidence to collect and stop conditions.
7. Do not write registers or change protection settings.
