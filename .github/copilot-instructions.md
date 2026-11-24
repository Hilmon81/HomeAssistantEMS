# Repository-wide Copilot instructions

## Operating principles

- Inspect the repository before proposing or implementing changes.
- Prefer existing architecture, libraries, naming, configuration and testing conventions.
- Never invent APIs, configuration keys, database columns, entity IDs, device registers, firmware behavior or requirements.
- Separate verified facts, repository evidence, assumptions and open questions.
- Keep changes focused. Do not refactor unrelated code.
- Do not add dependencies without explaining the need and checking existing alternatives.
- Add or update tests for changed behavior and run the relevant checks.
- Never expose secrets, tokens, personal data or production data in prompts, logs, tests or examples.
- AI output is a draft for human review. Never claim that a change is approved for production.

## Workflow

1. Discover repository structure and current behavior.
2. State the requested outcome and acceptance criteria.
3. Identify affected components and risks.
4. Produce an implementation and test plan.
5. Implement the smallest coherent change.
6. Run tests, static checks and security checks.
7. Report changed files, evidence, remaining risks and rollback.

## EMS safety rules

- Home Assistant is the preferred I/O and integration layer; heavy optimization belongs in a Python/.NET service when appropriate.
- Use one connection owner or serialized queue per physical Modbus device.
- Define power sign conventions explicitly: grid import/export and battery charge/discharge.
- Keep units explicit: W/kW, Wh/kWh, A, V, %, SEK/kWh and time-step duration.
- Never infer interval duration only from the number of Nord Pool price points; support hourly and 15-minute data.
- Treat Solcast and load forecasts as uncertain and use margins and re-optimization.
- Make control idempotent. Include deadband, minimum hold time, ramp limits, timeouts, stale-data checks and safe fallback.
- Create read-only observability before write control. Physical writes require verified documentation, current-value backup, rollback and explicit human confirmation.
- Never alter electrical protection, grid-code or certified safety parameters.

## Definition of done

- Acceptance criteria are mapped to implementation and tests.
- Relevant automated tests pass, or failures are documented with exact evidence.
- Security, configuration, migration and operational impacts are reviewed.
- EMS changes include sign/unit validation, stale-data behavior, feedback verification and rollback where applicable.
- Documentation and project profile are updated when interfaces or operational behavior change.
- The result is marked READY FOR HUMAN REVIEW, never APPROVED.
