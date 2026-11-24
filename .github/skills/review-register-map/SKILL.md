---
name: review-register-map
description: "Audit a Modbus register map for completeness, decoding and write safety."
disable-model-invocation: true
---
Audit the supplied register map. For each entry report:
`Name | Document address | Client address | FC | R/W | Data type | Words | Signed | Byte/word order | Scale | Unit | Valid range | Sign convention | Source/version | Status`.

Status must be verified, probable, unknown or must-not-write. Identify address-base, type, endian, scale, range and source gaps. Provide safe read-only tests. Do not propose a write test unless official documentation verifies the exact model, firmware, address and value semantics; even then leave execution behind an explicit human gate.
