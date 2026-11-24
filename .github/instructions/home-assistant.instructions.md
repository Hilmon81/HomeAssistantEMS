---
applyTo: "**/*.yaml,**/*.yml,**/custom_components/**,**/appdaemon/**,**/homeassistant/**"
---


Use modern Home Assistant syntax supported by the installed version. Prefer official local integrations. Do not invent entities or services. Keep YAML complete and correctly indented. Use availability/freshness checks, idempotent actions and safe fallback. Avoid simultaneous Modbus clients. For custom integrations, use a coordinator and diagnostics and separate the transport library from HA entities.
