---
name: release-review
description: Prepare an evidence-based release review for human approval.
disable-model-invocation: true
---
Review requirements, changed files, tests, security, migrations, configuration, observability and rollback. For EMS changes, verify sign/unit tests, stale-data behavior, write gates, feedback, watchdog, safe fallback and rollback test evidence. Do not approve. Return blockers, residual risks, deployment/rollback steps and READY or NOT READY FOR HUMAN REVIEW.
