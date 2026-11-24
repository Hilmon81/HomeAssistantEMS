---
applyTo: "**/*test*,**/*spec*,**/tests/**"
---


Tests must be deterministic and traceable to requirements. Avoid real production services or physical writes. Use fixed clocks where time matters. Include DST, missing data, stale data, communication failure, duplicate input, bounds and rollback cases. Preserve failing evidence; do not weaken assertions merely to pass.
