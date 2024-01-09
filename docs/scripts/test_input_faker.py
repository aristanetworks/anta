from inspect import isclass
from inspect import ismodule
from types import ModuleType
from typing import Any
from typing import get_args

from anta.models import AntaTest
from anta.tests import aaa
from anta.tests import configuration
from anta.tests import connectivity
from anta.tests import field_notices
from anta.tests import hardware
from anta.tests import interfaces
from anta.tests import logging
from anta.tests import mlag
from anta.tests import multicast
from anta.tests import profiles
from anta.tests import security
from anta.tests import snmp
from anta.tests import software
from anta.tests import stp
from anta.tests import system
from anta.tests import vxlan
from anta.tests.routing import bgp
from anta.tests.routing import generic
from anta.tests.routing import ospf
from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel
from yaml import safe_dump


def sanitize_inputs(inputs: Any) -> Any:
    if inputs == None:
        return
    elif isinstance(inputs, BaseModel):
        return sanitize_inputs(inputs.dict())
    elif isinstance(inputs, list):
        # TODO filter None
        return [sanitize_inputs(e) for e in inputs]
    elif isinstance(inputs, dict):
        res = {}
        for key, value in inputs.items():
            if (v := sanitize_inputs(value)) is not None:
                res[key] = v
        return res
    elif not isinstance(inputs, (int, bool, str)):
        return str(inputs)
    else:
        print(type(inputs), inputs)
        return inputs


def fake_input(test_class: type[AntaTest]) -> object | None:
    if hasattr(test_class, "Input") and issubclass(test_class.Input, AntaTest.Input):

        class InputFactory(ModelFactory[test_class.Input]):
            __random_seed__ = 1
            __randomize_collection_length__ = True
            __min_collection_length__ = 2
            __max_collection_length__ = 2

            # Always setting filters and result_overwrite to None for default
            filters = None
            result_overwrite = None
            # Setting default value for various keys
            manufacturers = ["AristaNetworks", "SomeOtherManufactuer"]
            vrf = "PROD"
            interface = intf = "Ethernet1"
            groups = ["group1", "group2"]
            methods = ["local", "group2"]
            vteps = servers = ["10.42.42.42", "172.16.66.6"]
            number = 42
            bindings = "10042: 42"
            vlans = {42, 666}
            detection_delay = 42
            errdisabled = True
            specific_mtu = [{"Ethernet1": 666}, {"Ethernet2": 2048}]
            reload_delay = reload_delay_non_mlag = recovery_delay_non_mlag = recovery_delay = 42
            ignored_interfaces = ["Ethernet42", "Ethernet43"]

            @classmethod
            def vlans(cls) -> Any:
                if (field := test_class.Input.model_fields.get("vlans")) is None:
                    return
                import typing

                print(field.annotation, field.annotation == typing.Dict, type(field.annotation))
                return {42, 666}

        inputs = sanitize_inputs(InputFactory.build().__dict__)

        return {test_class.__module__: [{test_class.__name__: inputs}]}
    return None


def find_tests(module: ModuleType) -> list[type[AntaTest]]:
    return module.AntaTest.__subclasses__()


if __name__ == "__main__":
    all_test_classes = [
        test
        for module in [
            aaa,
            configuration,
            connectivity,
            field_notices,
            hardware,
            interfaces,
            logging,
            mlag,
            multicast,
            profiles,
            security,
            snmp,
            software,
            stp,
            system,
            vxlan,
            bgp,
            generic,
            ospf,
        ]
        for test in find_tests(module)
    ]
    print(all_test_classes)

    for test_class in all_test_classes:
        print(safe_dump(fake_input(test_class)))
