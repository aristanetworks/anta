"""
Import all tests in the module at this level for backward compatibiity
until devel-tests branch is merged. When merged this file should be reverted
to an empty file
"""

# flake8: noqa
from .configuration import *
from .hardware import *
from .interfaces import *
from .mlag import *
from .multicast import *
from .profiles import *
from .routing.bgp import *
from .routing.generic import *
from .routing.ospf import *
from .software import *
from .system import *
from .vxlan import *
