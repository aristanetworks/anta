"""
Test functions related to various connectivity checks
"""
from __future__ import annotations

import logging
from typing import Any, Dict, cast

from anta.models import AntaTest, AntaTemplate

logger = logging.getLogger(__name__)


class VerifyReachability(AntaTest):
    """
    Test network reachability to one or many destination IP(s).

    Expected Results:
        * success: The test will pass if all destination IP(s) are reachable.
        * failure: The test will fail if one or many destination IP(s) are unreachable.
        * error: The test will give an error if the destination IP(s) or the source interface/IP(s) are not provided as template_params.
    """

    name = "VerifyReachability"
    description = "Test the network reachability to one or many destination IP(s)."
    categories = ["connectivity"]
    template = AntaTemplate(template="ping {dst} source {src} repeat 2")

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyReachability validation.
        """

        failures = []

        for index, command in enumerate(self.instance_commands):
            src, dst = (cast(Dict[str, str], command.template_params)["src"], cast(Dict[str, str], command.template_params)["dst"])

            command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[index].output)
            if "2 received" not in command_output["messages"][0]:
                failures.append((src, dst))

        if not failures:
            self.result.is_success()

        else:
            self.result.is_failure(f"Connectivity test failed for the following source-destination pairs: {failures}")
