#!/usr/bin/env python3

# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Prepare the compact NRFU catalog used by the README animation."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# The README animation is a short visual introduction, not a catalog coverage
# demonstration. Keep this allowlist explicit so additions cannot silently make
# the recording slow or noisy.
DEMO_TESTS = {
    "VerifyAPIHttpStatus",
    "VerifyAPIHttpsSSL",
    "VerifyAcctConsoleMethods",
    "VerifyAuthenMethods",
    "VerifyCPUUtilization",
    "VerifyChassisHealth",
    "VerifyCoredump",
    "VerifyDNSServers",
    "VerifyEOSVersion",
    "VerifyEnvironmentCooling",
    "VerifyEnvironmentPower",
    "VerifyFlashUtilization",
    "VerifyHostname",
    "VerifyIGMPSnoopingGlobal",
    "VerifyInterfaceErrDisabled",
    "VerifyInterfaceErrors",
    "VerifyInterfacesSpeed",
    "VerifyInterfacesStatus",
    "VerifyInventory",
    "VerifyLACPInterfacesStatus",
    "VerifyLLDPNeighbors",
    "VerifyMemoryUtilization",
    "VerifyMlagConfigSanity",
    "VerifyMlagInterfaces",
    "VerifyMlagStatus",
    "VerifyModuleStatus",
    "VerifyNTP",
    "VerifyPortChannels",
    "VerifyReloadCause",
    "VerifySSHStatus",
    "VerifySTPMode",
    "VerifySnmpStatus",
    "VerifyTcamProfile",
    "VerifyTelnetStatus",
    "VerifyTemperature",
    "VerifyTerminAttrVersion",
    "VerifyUptime",
    "VerifyVlanStatus",
    "VerifyVxlan1Interface",
    "VerifyZeroTouch",
}


def main() -> None:
    """Select deliberately fast tests from the example catalog."""
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    catalog = yaml.safe_load(source.read_text(encoding="utf-8"))

    found: set[str] = set()
    for module, tests in tuple(catalog.items()):
        selected = [test for test in tests if not DEMO_TESTS.isdisjoint(test)]
        for test in selected:
            found.update(DEMO_TESTS.intersection(test))
        if selected:
            catalog[module] = selected
        else:
            del catalog[module]

    if missing := DEMO_TESTS - found:
        msg = f"Demo tests not found in {source}: {', '.join(sorted(missing))}"
        raise RuntimeError(msg)

    destination.write_text(yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
