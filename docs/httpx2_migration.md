<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# ANTA httpx -> httpx2 Migration

## Overview

This document describes the completed migration of ANTA from `httpx` (encode/httpx) to `httpx2` (pydantic/httpx2), a fork maintained by Pydantic. The migration also involves:

- `httpcore` -> `httpcore2` (the transport layer)
- `pytest-httpx` -> `pytest-httpx2` (test mocking, wraps `respx` for httpcore2)
- `respx` remains but uses the `httpx2_mock` fixture from pytest-httpx2 (which targets `httpcore2` transports)

## Why httpx2?

httpx2 is a community fork of httpx, stewarded by Pydantic, created because httpx was seeing limited maintenance activity. httpx2 provides:

- Timely security updates and bug fixes
- Active maintenance under the Pydantic organization
- Near-identical API to httpx (drop-in replacement)
- New features: native SSE support, Headers union operators, truststore-based SSL

Current httpx2 version: **2.5.0** (forked from httpx 0.28.1).

## Import Style

All httpx2 usage follows the `import httpx2` style with fully qualified names (e.g. `httpx2.ConnectError`, `httpx2.HTTPError`) rather than `from httpx2 import ConnectError`. This makes it immediately clear where each symbol comes from when reading the code.

## Scope of Changes

### Summary Table

| Category | File Count | Complexity |
| --- | --- | --- |
| Source code (`asynceapi/`) | 4 files | Low - mechanical rename |
| Source code (`anta/`) | 3 files | Low - mechanical rename |
| Test files | 8 files | Medium - respx/pytest-httpx migration |
| Config files | 2 files | Low - dependency version changes |
| Total | **17 files** | |

---

## Source Code Changes

### 1. `asynceapi/device.py` — Core eAPI Client

**Current state:** `Device` subclasses `httpx.AsyncClient` and uses `httpx.URL`, `httpx.BasicAuth`, `httpx.Auth`, `httpx.HTTPError`, `httpx.Request`.

**Changes required:**

```python
# Before
import httpx
class Device(httpx.AsyncClient):
    ...
    kwargs.setdefault("base_url", httpx.URL(...))
    auth_object = httpx.BasicAuth(username, password)
    await self.post(..., auth=httpx.Auth(), ...)
    except httpx.HTTPError as exc:

# After
import httpx2
class Device(httpx2.AsyncClient):
    ...
    kwargs.setdefault("base_url", httpx2.URL(...))
    auth_object = httpx2.BasicAuth(username, password)
    await self.post(..., auth=httpx2.Auth(), ...)
    except httpx2.HTTPError as exc:
```

**Decision:** Straight rename. The httpx2 `AsyncClient`, `URL`, `BasicAuth`, `Auth`, and `HTTPError` APIs are identical to httpx.

**Note on `verify=False`:** ANTA explicitly sets `verify=False` (line 117) for device connections, so the httpx2 truststore change (from certifi to OS trust store) has **no impact** — SSL verification is disabled for eAPI connections.

### 2. `asynceapi/_auth.py` — Session Cookie Authentication

**Current state:** `EapiSessionAuth` subclasses `httpx.Auth` and uses `httpx.Request`, `httpx.Response` in type annotations and the auth flow generator protocol.

**Changes required:**

```python
# Before
import httpx
class EapiSessionAuth(httpx.Auth):
    def sync_auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
    async def async_auth_flow(self, request: httpx.Request) -> AsyncGenerator[httpx.Request, httpx.Response]:
        login_request = httpx.Request("POST", ...)

# After
import httpx2
class EapiSessionAuth(httpx2.Auth):
    def sync_auth_flow(self, request: httpx2.Request) -> Generator[httpx2.Request, httpx2.Response, None]:
    async def async_auth_flow(self, request: httpx2.Request) -> AsyncGenerator[httpx2.Request, httpx2.Response]:
        login_request = httpx2.Request("POST", ...)
```

**Decision:** Straight rename. The `httpx2.Auth` base class and its `sync_auth_flow`/`async_auth_flow` protocol are identical to httpx.

### 3. `asynceapi/errors.py` — Exception Definitions

**Current state:** Imports `httpx` for the `EapiTransportError` alias.

```python
# Before
import httpx
EapiTransportError = httpx.HTTPStatusError

# After
import httpx2
EapiTransportError = httpx2.HTTPStatusError
```

**Decision:** Straight rename. The exception hierarchy in httpx2 is identical to httpx.

### 4. `asynceapi/aio_portcheck.py` — Port Check Utility

**Current state:** `TYPE_CHECKING` import of `httpx.URL`.

```python
# Before
from httpx import URL

# After (TYPE_CHECKING only)
import httpx2  # under TYPE_CHECKING
# usage: url: httpx2.URL
```

**Decision:** Qualified import under `TYPE_CHECKING`. Only a type annotation, no runtime behavior change.

### 5. `anta/device.py` — Device Abstraction

**Current state:** Imports `httpx` exceptions and `httpcore.ConnectError`.

```python
# Before
import httpcore
from httpx import ConnectError, HTTPError, TimeoutException

# After
import httpcore2
import httpx2
# usage: except httpx2.ConnectError, httpx2.HTTPError, httpx2.TimeoutException
```

Also update the `_handle_connect_error` method (line 650):

```python
# Before
if (isinstance(exc := e.__cause__, httpcore.ConnectError) and ...

# After
if (isinstance(exc := e.__cause__, httpcore2.ConnectError) and ...
```

**Internal attribute access (line 535):**

```python
self._client._transport._pool._max_connections
```

This accesses httpx/httpcore internals. In httpx2, the transport layer uses `httpcore2` but the internal structure is the same. The existing `try/except AttributeError` guard handles any structural changes gracefully. **No change needed** beyond what the rename naturally provides.

**Decision:** Straight rename of imports. The `httpcore` -> `httpcore2` rename is required here too.

### 6. `anta/cli/exec/utils.py` — CLI Exec Helpers

**Current state:** Imports `ConnectError`, `HTTPError` from httpx.

```python
# Before
from httpx import ConnectError, HTTPError

# After
import httpx2
# usage: except httpx2.ConnectError, httpx2.HTTPError
```

**Decision:** Straight rename.

### 7. `anta/logger.py` — Logger Configuration

**Current state:** Silences the httpx logger.

```python
# Before
logging.getLogger("httpx").setLevel(logging.WARNING)

# After
logging.getLogger("httpx2").setLevel(logging.WARNING)
```

**Decision:** The httpx2 library uses `httpx2` as its logger name. Straight rename.

### 8. `anta/settings.py` — HTTPX Settings

**Current state:** `AntaHttpxSettings` manages `ANTA_HTTPX_TRUST_ENV` environment variable and documentation references "HTTPX client".

**Decision:** No code changes needed. The `trust_env` parameter exists identically in httpx2's `AsyncClient`. The setting name `ANTA_HTTPX_TRUST_ENV` and class name `AntaHttpxSettings` can remain as-is or be renamed — this is a naming preference, not a functional requirement. We recommend keeping the existing names to avoid a user-facing breaking change on the environment variable.

---

## Test Changes

### 9. Mocking Strategy: httpx2_mock Fixture

ANTA tests previously used two mocking approaches for HTTP:

1. **`respx`** — Used in 7 test files, directly mocking httpx routes via `respx.mock`, `respx.post()`, etc.
2. **`pytest-httpx`** — Used in 1 test file (`tests/units/asynceapi/test_device.py`) via the `httpx_mock: HTTPXMock` fixture.

#### Key Decision: Use `httpx2_mock` Fixture Everywhere

The migration standardized on the `httpx2_mock` fixture from `pytest-httpx2`, which provides a `respx.Router` configured with `using="httpcore2"`. This was chosen over direct `respx.mock(using="httpcore2")` usage because:

1. **Global vs local router problem**: `respx.mock(using="httpcore2")` creates a local router, but `respx.post(...)` adds routes to the **global** router. This mismatch caused routes to not be matched. Using the fixture avoids this entirely.
2. **Fixture composability**: The `inventory` fixture (used by most tests) now depends on `httpx2_mock`, so all tests that use `inventory` automatically get httpcore2 mocking. Tests can add additional routes to the same `httpx2_mock` router.
3. **Consistent API**: All tests use `httpx2_mock.post(...)`, `httpx2_mock.head(...)` etc. instead of mixing global and local respx APIs.

#### Custom `httpx2_mock` Fixture Override

The `tests/conftest.py` overrides the default `httpx2_mock` fixture to set `assert_all_called=False` by default, matching the previous `respx.mock` behavior where uncalled routes don't cause test failures. This is a workaround for [pytest-httpx2#4](https://github.com/lundberg/pytest-httpx2/issues/4):

```python
@pytest.fixture
def httpx2_mock(request: pytest.FixtureRequest) -> Iterator[respx.Router]:
    options = {}
    if (marker := request.node.get_closest_marker("httpx2")) is not None:
        options.update(marker.kwargs)
    options.setdefault("using", "httpcore2")
    options.setdefault("assert_all_called", False)
    with respx.mock(**options) as router:
        yield router
```

#### `side_effect` with Response Objects

When using `respx` `side_effect` with `Response` objects, those responses must be `httpx.Response` (not `httpx2.Response`), because respx internally validates `isinstance(response, httpx.Response)`. This only affects one test in `test_device.py` where `side_effect=[httpx.Response(200, ...), httpx.Response(401)]` is used. This is a known respx limitation tracked in [respx#316](https://github.com/lundberg/respx/issues/316) and [respx#324](https://github.com/lundberg/respx/issues/324).

### 10. pytest-httpx -> respx.Router API Migration

The 3 tests that used `pytest-httpx`'s `HTTPXMock.add_response()` were rewritten to use `respx.Router` patterns with `respx.mock(using="httpcore2")` context managers:

```python
# Before
httpx_mock.add_response(json=SUCCESS_EAPI_RESPONSE)

# After
with respx.mock(using="httpcore2") as respx_mock:
    respx_mock.post(path="/command-api").respond(json=SUCCESS_EAPI_RESPONSE)
```

---

## Configuration Changes

### 11. `pyproject.toml` — Dependencies

```toml
# Before
dependencies = [
    ...
    "httpx>=0.27.0",
    ...
]

[dependency-groups]
dev = [
    ...
    "pytest-httpx>=0.36.2",
    ...
]

# After
dependencies = [
    ...
    "httpx2>=2.2.0",
    ...
]

[dependency-groups]
dev = [
    ...
    "pytest-httpx2>=1.0.0",
    ...
]
```

**Note:** `respx` remains as a dependency (it's likely already pulled in transitively by pytest-httpx, but should be listed explicitly since we use it directly). Minimum version should be `>=0.23.1` (the version tested with pytest-httpx2).

Also add pytest plugin activation:

```toml
[tool.pytest.ini_options]
addopts = "-p pytest_httpx2"
```

### 12. `.pre-commit-config.yaml`

```yaml
# Before
- pytest-httpx>=0.30.0

# After
- pytest-httpx2>=1.0.0
```

---

## Risk Assessment

### Low Risk

- **Import renames** (11 source/test files): Purely mechanical, no behavioral change. httpx2's public API is identical to httpx.
- **Exception hierarchy**: Identical between httpx and httpx2. All `except` blocks catch the same exception types.
- **Auth base class**: `httpx2.Auth` has the same `sync_auth_flow`/`async_auth_flow` protocol.
- **AsyncClient subclassing**: `Device(httpx2.AsyncClient)` works identically.

### Medium Risk

- **respx mocking with httpcore2**: All `respx.mock` usage must target `httpcore2` transports. If any test forgets `using="httpcore2"`, respx will patch the old `httpcore` (if installed) or fail.
- **pytest-httpx -> respx Router API**: The 3 tests using `HTTPXMock.add_response()` need manual rewrite to use `respx.Router` patterns. The APIs are different but the tests are simple.
- **httpcore2 internal access** (`anta/device.py:535`): `self._client._transport._pool._max_connections` accesses httpcore internals. In httpcore2, the internal structure is preserved, and the existing `try/except AttributeError` guard makes this safe.

### Low-to-No Risk

- **SSL/truststore change**: ANTA uses `verify=False` for eAPI, so the truststore migration has zero impact.
- **Deprecation warnings**: httpx2 deprecates `verify=<str>`, `cert=...`, `URL.raw`, per-request `cookies=`, and `data=<bytes>`. ANTA uses none of these deprecated patterns (it passes `verify=False` as a boolean, doesn't use `cert`, and uses `json=` for POST bodies).

---

## Migration Order

Recommended order for the migration:

1. **Update `pyproject.toml`** — Change dependencies from `httpx`/`pytest-httpx` to `httpx2`/`pytest-httpx2`. Add `respx` explicitly if not already present. Add `-p pytest_httpx2` to pytest addopts.

2. **Update `.pre-commit-config.yaml`** — Change `pytest-httpx` to `pytest-httpx2`.

3. **Migrate `asynceapi/` package** (4 files) — Rename all `httpx` imports to `httpx2`. This is the core change since `asynceapi.Device` subclasses `httpx.AsyncClient`.

4. **Migrate `anta/` source** (3 files) — Rename imports in `device.py`, `cli/exec/utils.py`, and `logger.py`. Change `httpcore` to `httpcore2` in `device.py`.

5. **Migrate test files** (8 files) — Rename `httpx` imports, add `using="httpcore2"` to all `respx.mock` calls, rewrite the 3 `HTTPXMock` tests to use `respx.Router`.

6. **Run test suite** — Verify all tests pass with the new dependencies.

---

## File-by-File Change Inventory

| # | File | Changes |
| --- | --- | --- |
| 1 | `pyproject.toml` | `httpx>=0.27.0` -> `httpx2>=2.2.0`; `pytest-httpx>=0.36.2` -> `pytest-httpx2>=1.0.0`; add `-p pytest_httpx2` to addopts |
| 2 | `.pre-commit-config.yaml` | `pytest-httpx>=0.30.0` -> `pytest-httpx2>=1.0.0` |
| 3 | `asynceapi/device.py` | `import httpx` -> `import httpx2`; all `httpx.` references -> `httpx2.` |
| 4 | `asynceapi/_auth.py` | `import httpx` -> `import httpx2`; all `httpx.` references -> `httpx2.` |
| 5 | `asynceapi/errors.py` | `import httpx` -> `import httpx2`; `httpx.HTTPStatusError` -> `httpx2.HTTPStatusError` |
| 6 | `asynceapi/aio_portcheck.py` | `from httpx import URL` -> `import httpx2` (TYPE_CHECKING); `URL` -> `httpx2.URL` |
| 7 | `anta/device.py` | `import httpcore` -> `import httpcore2`; `from httpx import ...` -> `import httpx2`; all exceptions qualified as `httpx2.X` |
| 8 | `anta/cli/exec/utils.py` | `from httpx import ...` -> `import httpx2`; exceptions qualified as `httpx2.X` |
| 9 | `anta/logger.py` | `"httpx"` -> `"httpx2"` logger name |
| 10 | `anta/settings.py` | No code changes (env var `ANTA_HTTPX_TRUST_ENV` kept as-is) |
| 11 | `tests/conftest.py` | Override `httpx2_mock` fixture with `assert_all_called=False`; `inventory` fixture uses `httpx2_mock` |
| 12 | `tests/units/asynceapi/test_device.py` | `import httpx2`; migrate `HTTPXMock` -> `respx.mock(using="httpcore2")`; qualify `httpx2.X` |
| 13 | `tests/units/asynceapi/test__auth.py` | `import httpx` -> `import httpx2`; all `httpx.Request`/`httpx.Response` -> `httpx2.` |
| 14 | `tests/units/asynceapi/test_errors.py` | `import httpx` -> `import httpx2`; assertions against `httpx2.HTTPStatusError` |
| 15 | `tests/units/test_device.py` | `from httpx import ...` -> `import httpx2`; all exceptions qualified as `httpx2.X` |
| 16 | `tests/units/test__runner.py` | Use `httpx2_mock` fixture instead of `@respx.mock` decorator |
| 17 | `tests/units/cli/exec/test_utils.py` | Use `httpx2_mock` fixture; `respx_mock.post()` -> `httpx2_mock.post()` |
| 18 | `tests/units/cli/test__init__.py` | `{"httpx": None}` -> `{"httpx2": None}`; match string update |
| 19 | `tests/integration/test_run_eos_commands.py` | Use `httpx2_mock` fixture |
| 20 | `tests/benchmark/conftest.py` | Removed global `respx.post()` route setup |
| 21 | `tests/benchmark/test_anta.py` | Use `httpx2_mock` fixture; `httpx2_mock.clear()` before setting `eapi_response` side_effect |
| 22 | `tests/benchmark/utils.py` | `import httpx2` (TYPE_CHECKING); `eapi_response` returns `httpx.Response` (respx requirement) |
| 23 | `docs/advanced_usages/env-vars.md` | Update HTTPX -> httpx2 references and documentation URL |
| 24 | `docs/faq.md` | Update timeouts documentation URL |

---

## Resolved Decisions

1. **Minimum httpx2 version**: `httpx2>=2.2.0` (matches pytest-httpx2's tested version).
2. **respx version pin**: `>=0.23.1` (already in pyproject.toml).
3. **Environment variable naming**: `ANTA_HTTPX_TRUST_ENV` kept as-is to avoid user-facing breaking change.
4. **Import style**: `import httpx2` with fully qualified names (`httpx2.ConnectError`, `httpx2.HTTPError`) for clarity.
5. **Documentation**: Updated docs to reference httpx2 and the new documentation URL at `httpx2.pydantic.dev`.
