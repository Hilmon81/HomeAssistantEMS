---
name: fix-bug
description: Diagnose and fix a defect with reproduction evidence and regression tests.
disable-model-invocation: true
---
Reproduce the defect before changing code where possible. Trace the failure to the responsible layer. For EMS problems inspect physical/transport, protocol, decoding, application concurrency and control logic separately. Implement the smallest safe fix, add a regression test, run relevant checks and document rollback and residual risk.
