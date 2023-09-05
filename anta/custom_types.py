# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Module that provides predefined types for AntaTest.Input instances
"""
from typing import Literal

from pydantic import conint
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated, TypeAlias


def aaa_group_prefix(v: str) -> str:
    """Prefix the AAA method with 'group' if it is known"""
    built_in_methods = ["local", "none", "logging"]
    return f"group {v}" if v not in built_in_methods and not v.startswith("group ") else v


AAAAuthMethod = Annotated[str, AfterValidator(aaa_group_prefix)]
Vlan: TypeAlias = conint(ge=0, le=4094)  # type: ignore
TestStatus = Literal["unset", "success", "failure", "error", "skipped"]
