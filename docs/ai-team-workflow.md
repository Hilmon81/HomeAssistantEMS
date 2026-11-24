# AI team workflow

## Normal feature
1. Project Manager defines outcome and acceptance criteria.
2. Architect maps impact and interfaces.
3. Relevant implementation agent proposes the smallest change.
4. QA creates tests; Security reviews trust and privilege.
5. Code Reviewer compares evidence to requirements.
6. A human reviews and decides merge/release.

## EMS or Home Assistant feature
1. Classify read-only, simulation, configuration or physical write.
2. EMS Expert validates model, signs, units, constraints and fallback.
3. Modbus Expert validates transport/register evidence when applicable.
4. Home Assistant Expert validates entities, availability, automations and connection ownership.
5. Implement read-only observability first.
6. Test with simulator/fakes.
7. Add an explicit enable/armed signal and safe default.
8. A human decides whether a limited write test may occur.
9. Verify feedback and rollback before soak testing.
