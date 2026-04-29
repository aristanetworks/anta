<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

ANTA exposes several environment variables that allow you to configure its behavior without modifying code or CLI flags. These variables are read at startup.

## Summary

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `ANTA_HTTPX_TRUST_ENV` | `true` | Allow the HTTPX client to read proxy settings from the environment |

---

## `ANTA_HTTPX_TRUST_ENV`

Controls whether the HTTPX client reads proxy configuration from the environment (e.g. `HTTP_PROXY`, `HTTPS_PROXY`). Set to `false` to disable this behavior.

```bash
export ANTA_HTTPX_TRUST_ENV=false
anta nrfu table
```

---
