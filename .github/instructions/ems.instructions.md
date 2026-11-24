---
applyTo: "**/ems/**,**/optimizer/**,**/*energy*,**/*battery*,**/*forecast*,**/*dispatch*"
---


Define signs and units before implementation. Model time steps explicitly and support 60- and 15-minute intervals. Preserve source timestamps and data quality. Optimization must include SoC dynamics, efficiencies, import/export, constraints, reserve and a feasible fallback. Validate and clamp outputs before commands. Include desired/applied/feedback, watchdog, stale-data handling and rollback to safe local operation.
