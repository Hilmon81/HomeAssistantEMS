---
name: onboard-repository
description: Perform a read-only onboarding analysis for the AI development team.
disable-model-invocation: true
---
Perform a read-only onboarding of this repository. Do not modify production code.

1. Read repository instructions and documentation.
2. Identify languages, frameworks, dependencies, tests, databases, deployment and integrations.
3. Map EMS, Home Assistant and Modbus components if present.
4. Identify the real sign conventions, units, time resolution and connection ownership, or mark them unknown.
5. Compare findings with `docs/project/project-profile.md` and list gaps.
6. Identify safety-sensitive paths and current write capabilities.
7. Recommend which agents should own each area.
8. Return a prioritized setup plan and proposed documentation changes. Do not implement them.
