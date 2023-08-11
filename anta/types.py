"""
Module that provides predefined types for AntaTest.Input instances
"""
from typing import Literal
from pydantic import conint
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated


def aaa_group_prefix(v: str) -> str:
    built_in_methods = ["local", "none", "logging"]
    return f"group {v}" if v not in built_in_methods and not v.startswith("group ") else v


AAAAuthMethod = Annotated[str, AfterValidator(aaa_group_prefix)]
Vlan = conint(ge=0, le=4094)
TestStatus = Literal["unset", "success", "failure", "error", "skipped"]
