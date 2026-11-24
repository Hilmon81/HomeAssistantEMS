---
applyTo: "**/Dockerfile*,**/docker-compose*.yml,**/compose*.yml,**/.dockerignore"
---


Use minimal pinned images consistent with the repository. Run as non-root when possible. Add health checks and graceful shutdown. Mount configuration/secrets safely and document persistence. Control services must start unarmed unless a reviewed design says otherwise. Define rollback to the prior image/configuration.
