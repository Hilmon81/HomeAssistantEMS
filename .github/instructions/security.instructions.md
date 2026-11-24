---
applyTo: "**/*auth*,**/*security*,**/*secret*,**/*token*,**/*permission*"
---


Use least privilege, validate inputs and keep secrets out of source, logs and examples. Treat device control, HA service calls, Modbus writes and cloud API access as privileged. Document trust boundaries, required permissions and revocation/rotation. Never allow AI to approve risk acceptance or production release.
