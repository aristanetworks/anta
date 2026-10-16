# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Opt-in pytest plugin exporting evidence after all benchmark callbacks have finished."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Retain references to existing session fixtures; do not build another catalog before measurement.
_FIXTURES: dict[str, Any] = {}


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(
    fixturedef: pytest.FixtureDef[Any],
    request: pytest.FixtureRequest,  # noqa: ARG001
) -> Generator[None, Any, Any]:
    """Observe existing session fixtures without changing their setup or benchmark callbacks."""
    value = yield
    if fixturedef.argname in {"anta_mock_env", "session_results"}:
        _FIXTURES[fixturedef.argname] = value
    return value


def pytest_sessionfinish(  # noqa: C901  # pylint: disable=too-many-locals
    session: pytest.Session,
    exitstatus: int,
) -> None:
    """Serialize workload and measured-result evidence only after the entire session."""
    # Defer diagnostic imports and serialization until after the final measurement.
    import hashlib  # noqa: PLC0415
    import json  # noqa: PLC0415
    import os  # noqa: PLC0415
    import sys  # noqa: PLC0415
    from collections import Counter  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    output = Path(os.environ["ANTA_MEMORY_EVIDENCE_DIR"])
    output.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, Any] = {
        "exitstatus": int(exitstatus),
        "pid": os.getpid(),
        "runner_mode": os.environ.get("CODSPEED_RUNNER_MODE"),
        "collected_order": [item.nodeid for item in session.items],
        "cases": {},
    }

    def encode(value: Any) -> bytes:  # noqa: ANN401 - JSON data has heterogeneous recursive values.
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

    if (env := _FIXTURES.get("anta_mock_env")) is not None:
        definitions = [
            {"test": f"{definition.test.__module__}.{definition.test.__qualname__}", "inputs": definition.inputs.model_dump(mode="json")}
            for definition in env.catalog.tests
        ]
        workload = {
            "definitions": definitions,
            "responses": [{"test": test, "case": case, "data": data} for (test, case), data in sorted(env.eos_data_catalog.items())],
        }
        raw = encode(workload)
        (output / "catalog.json").write_bytes(raw)
        evidence["raw_catalog_sha256"] = hashlib.sha256(raw).hexdigest()
        # This fixture derives one-day-old timestamps at import. Normalize only those exact
        # values in its response data for comparison; retain every raw value in catalog.json.
        reference = sys.modules["tests.units.anta_tests.test_interfaces"].timestamp_one_day_ago
        canonical = json.loads(raw)
        normalized = 0

        def normalize(value: Any) -> Any:  # noqa: ANN401 - Walk a JSON response without changing its other values.
            nonlocal normalized
            if isinstance(value, list):
                return [normalize(item) for item in value]
            if isinstance(value, dict):
                result = {}
                for key, item in value.items():
                    if key == "lastStatusChangeTimestamp" and item == reference:
                        result[key] = "<fixture:one_day_ago>"
                        normalized += 1
                    else:
                        result[key] = normalize(item)
                return result
            return value

        for response in canonical["responses"]:
            if response["test"] == "VerifyInterfacesCounterDetails":
                response["data"] = normalize(response["data"])
        evidence["normalized_one_day_ago_timestamps"] = normalized
        evidence["catalog_count"] = env.tests_count
        evidence["catalog_sha256"] = hashlib.sha256(encode(canonical)).hexdigest()

    for case, manager in _FIXTURES.get("session_results", {}).items():
        # The current runner inserts gather() results in coroutine scheduling order.
        # This observes the returned measured invocation, not native warm-up invocations.
        results = [{"device": result.name, "test": result.test, "case": result.custom_field, "status": result.result} for result in manager.results]
        order = [{key: value for key, value in result.items() if key != "status"} for result in results]
        evidence["cases"][case] = {
            "count": len(results),
            "statuses": dict(Counter(result["status"] for result in results)),
            "order_sha256": hashlib.sha256(encode(order)).hexdigest(),
            "results": results,
        }

    (output / "session.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
