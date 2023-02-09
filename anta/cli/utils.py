#!/usr/bin/python
# coding: utf-8 -*-

"""
Utils functions to use with anta.cli.cli module.
"""

import logging

from rich.logging import RichHandler

logger = logging.getLogger(__name__)


def setup_logging(level: str = "info") -> None:
    """
    Configure logging for check-devices execution

    Helpers to set logging for
    * anta.inventory
    * anta.result_manager
    * check-devices

    Args:
        level (str, optional): level name to configure. Defaults to 'critical'.
    """
    loglevel = getattr(logging, level.upper())

    FORMAT = "%(message)s"
    logging.basicConfig(
        level=loglevel, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    logging.getLogger("anta.inventory").setLevel(loglevel)
    logging.getLogger("anta.result_manager").setLevel(loglevel)

    logging.getLogger("anta.reporter").setLevel(logging.CRITICAL)
    logging.getLogger("anta.tests").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.configuration").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.hardware").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.interfaces").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.mlag").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.multicast").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.profiles").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.system").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.software").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.vxlan").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.routing.generic").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.routing.bgp").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.routing.ospf").setLevel(logging.ERROR)

    logger.setLevel(loglevel)
