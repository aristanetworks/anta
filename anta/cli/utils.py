#!/usr/bin/python
# coding: utf-8 -*-

"""
Utils functions to use with anta.cli.cli module.
"""

import logging

from rich.logging import RichHandler

logger = logging.getLogger(__name__)
# For logs triggered before setup_logging is called
FORMAT = "%(message)s"
logging.basicConfig(format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])


def setup_logging(level: str = "info") -> None:
    """
    Configure logging

    Args:
        level (str, optional): level name to configure. Defaults to 'critical'.
    """
    loglevel = getattr(logging, level.upper())
    logging.getLogger("anta").setLevel(loglevel)
