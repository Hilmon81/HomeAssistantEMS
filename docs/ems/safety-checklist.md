# EMS and Modbus safety checklist

## Before any physical write
- [ ] Exact model and firmware are known.
- [ ] Register/interface and value semantics are verified in the correct document version.
- [ ] Address base, function code, data type, words, signedness, order, scale and unit are verified.
- [ ] Valid range and physical consequence are known.
- [ ] Current value is read and logged.
- [ ] Rollback value or safe local mode is defined and tested where possible.
- [ ] No competing writer exists.
- [ ] Stale input, timeout and watchdog behavior are defined.
- [ ] Command is clamped and rate-limited.
- [ ] Human explicitly authorizes the bounded test.
- [ ] Electrical protection/grid-code settings are out of scope.

If any item is unchecked, remain read-only or simulated.
