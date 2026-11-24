---
applyTo: "**/*.py,**/pyproject.toml,**/requirements*.txt"
---


Follow the repository Python version, dependency manager, linting and typing conventions. Use type hints, structured logging, timeouts and bounded retry with backoff. Keep pure calculations separate from I/O. Normalize timestamps explicitly. Validate configuration and units. Hardware-facing code requires fakes/simulators and must default to read-only or unarmed operation.
