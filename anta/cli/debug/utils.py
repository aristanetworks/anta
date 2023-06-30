#!/usr/bin/python
# coding: utf-8 -*-
"""
Utils functions to use with anta.cli.debug module.
"""

from anta.models import AntaTest, AntaTestCommand


class RunArbitraryCommand(AntaTest):

    """
    Run an EOS command and return result
    Based on AntaTest to build relevant output for pytest
    """

    name = "Run aributrary EOS command"
    description = "To be used only with anta debug commands"
    commands = [AntaTestCommand(command="show version")]
    categories = ["debug"]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Fake test function
        CLI should only call self.collect()
        """
