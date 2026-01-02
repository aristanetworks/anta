# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.field_notices."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.field_notices import VerifyFieldNotice44Resolution, VerifyFieldNotice72Resolution
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyFieldNotice44Resolution, "success"): {
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}, {"name": "NotAboot", "version": "Aboot-veos-8.0.0-3255441"}],
                },
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyFieldNotice44Resolution, "failure-4.0"): {
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {"deviations": [], "components": [{"name": "Aboot", "version": "Aboot-veos-4.0.1-3255441"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device is running incorrect version of aboot 4.0.1"]},
    },
    (VerifyFieldNotice44Resolution, "failure-4.1"): {
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {"deviations": [], "components": [{"name": "Aboot", "version": "Aboot-veos-4.1.0-3255441"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device is running incorrect version of aboot 4.1.0"]},
    },
    (VerifyFieldNotice44Resolution, "failure-6.0"): {
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {"deviations": [], "components": [{"name": "Aboot", "version": "Aboot-veos-6.0.1-3255441"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device is running incorrect version of aboot 6.0.1"]},
    },
    (VerifyFieldNotice44Resolution, "failure-6.1"): {
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {"deviations": [], "components": [{"name": "Aboot", "version": "Aboot-veos-6.1.1-3255441"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device is running incorrect version of aboot 6.1.1"]},
    },
    (VerifyFieldNotice44Resolution, "skipped-model"): {
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "vEOS-lab",
                "details": {"deviations": [], "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Device is not impacted by FN044"]},
    },
    (VerifyFieldNotice44Resolution, "failure-no-aboot-component"): {
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {"deviations": [], "components": [{"name": "NotAboot", "version": "Aboot-veos-4.0.1-3255441"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Aboot component not found"]},
    },
    (VerifyFieldNotice72Resolution, "success-JPE"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JPE2130000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "7"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS, "messages": ["FN72 is mitigated"]},
    },
    (VerifyFieldNotice72Resolution, "success-JAS"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "7"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS, "messages": ["FN72 is mitigated"]},
    },
    (VerifyFieldNotice72Resolution, "success-K-JPE"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JPE2133000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "7"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS, "messages": ["FN72 is mitigated"]},
    },
    (VerifyFieldNotice72Resolution, "success-K-JAS"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JAS2040000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "7"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS, "messages": ["FN72 is mitigated"]},
    },
    (VerifyFieldNotice72Resolution, "skipped-Serial"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "BAN2040000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "7"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Device not exposed"]},
    },
    (VerifyFieldNotice72Resolution, "skipped-Platform"): {
        "eos_data": [
            {"modelName": "DCS-7150-52-CL", "serialNumber": "JAS0040000", "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "5"}]}}
        ],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Platform is not impacted by FN072"]},
    },
    (VerifyFieldNotice72Resolution, "skipped-range-JPE"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JPE2131000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "5"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Device not exposed"]},
    },
    (VerifyFieldNotice72Resolution, "skipped-range-K-JPE"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JPE2134000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "5"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Device not exposed"]},
    },
    (VerifyFieldNotice72Resolution, "skipped-range-JAS"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2041000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "5"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Device not exposed"]},
    },
    (VerifyFieldNotice72Resolution, "skipped-range-K-JAS"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JAS2041000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "5"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Device not exposed"]},
    },
    (VerifyFieldNotice72Resolution, "failed-JPE"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JPE2133000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "5"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device is exposed to FN72"]},
    },
    (VerifyFieldNotice72Resolution, "failed-JAS"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm1", "version": "5"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device is exposed to FN72"]},
    },
    (VerifyFieldNotice72Resolution, "error"): {
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {"deviations": [], "components": [{"name": "FixedSystemvrm2", "version": "5"}]},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Error in running test - Component FixedSystemvrm1 not found in 'show version"]},
    },
}
