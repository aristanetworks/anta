# hooks.py
import importlib
import logging
from inspect import isclass, ismodule
from types import ModuleType
from typing import Any, get_args

from mkdocs import plugins
from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel
from yaml import safe_dump

from anta.models import AntaTest
from anta.tests import aaa, configuration, connectivity, field_notices, hardware, interfaces, mlag, multicast, profiles, security, snmp, software, stp, system, vxlan
from anta.tests.routing import bgp, generic, ospf

# from anta.tests import logging

LOGGER = logging.getLogger(__name__)


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


def generate_test_input(test_class: type[AntaTest]) -> dict | None:
    if hasattr(test_class, "Input") and issubclass(test_class.Input, AntaTest.Input):

        class InputFactory(ModelFactory[test_class.Input]):
            # TODO complete this
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
            bindings = {10042: 42, 10666: 666}
            detection_delay = 42
            errdisabled = True
            specific_mtu = [{"Ethernet1": 666}, {"Ethernet2": 2048}]
            reload_delay = reload_delay_non_mlag = recovery_delay_non_mlag = recovery_delay = 42
            ignored_interfaces = ["Ethernet42", "Ethernet43"]

            # @classmethod
            # def vlans(cls) -> Any:
            #    if (field := test_class.Input.model_fields.get("vlans")) is None:
            #        return
            #    import typing

            #    print(field.annotation, field.annotation == typing.Dict, type(field.annotation))
            #    # TODO return stuff depending on the type of the field.annotation or find a better way
            #    return {42, 666}

        try:
            inputs = sanitize_inputs(InputFactory.build().__dict__)
        except Exception:
            inputs = {}

        return {test_class.__module__: [{test_class.__name__: inputs}]}
    return None


def find_tests(module: ModuleType) -> list[type[AntaTest]]:
    return module.AntaTest.__subclasses__()


def input_to_yaml(test_class: type[AntaTest]) -> str:
    return safe_dump(generate_test_input(test_class))


# This does not work because of mkdocstrings recreating its own Jinja2 Environment
# @plugins.event_priority(1000)
# def on_env(env, config, files, **kwargs):
#    env.filters["generate"] = input_to_yaml
#    return env

# This does not work because can only extend mkdocstings handler with template location but cannot overwrite today the update_env
# def update_env(md: Markdown, config: dict) -> None
#     """
#     """
#     super().update_env(md, config)
#     self.env.trim_blocks = True
#     self.env.lstrip_blocks = True
#     self.env.keep_trailing_newline = False
#     self.env.filters["split_path"] = rendering.do_split_path
#     self.env.filters["crossref"] = rendering.do_crossref
#     self.env.filters["multi_crossref"] = rendering.do_multi_crossref
#     self.env.filters["order_members"] = rendering.do_order_members
#     self.env.filters["format_code"] = rendering.do_format_code
#     self.env.filters["format_signature"] = rendering.do_format_signature
#     self.env.filters["format_attribute"] = rendering.do_format_attribute
#     self.env.filters["filter_objects"] = rendering.do_filter_objects
#     self.env.filters["stash_crossref"] = lambda ref, length: ref
#     self.env.filters["get_template"] = rendering.do_get_template
#     self.env.filters["as_attributes_section"] = rendering.do_as_attributes_section
#     self.env.filters["as_functions_section"] = rendering.do_as_functions_section
#     self.env.filters["as_classes_section"] = rendering.do_as_classes_section
#     self.env.filters["as_modules_section"] = rendering.do_as_modules_section
#     self.env.filters["as_modules_section"] = rendering.do_as_modules_section
#     self.env.filters["generare"] = input_to_yaml
#     self.env.tests["existing_template"] = lambda template_name: template_name in self.env.list_templates()

import ast
import inspect

from griffe import Class, Docstring, Extension, Object, ObjectNode, dynamic_import, get_logger


class GenerateInput(Extension):
    def on_class_instance(self, node: ast.AST | ObjectNode, cls: Class):
        # Only for subclass of AntaTest
        if "AntaTest" in [base.id for base in node.bases if hasattr(base, "id")]:
            LOGGER.debug(f"Generating input for {cls.path}")
            module = importlib.import_module(cls.module.path)
            test_class = getattr(module, cls.name)
            cls.anta_input = input_to_yaml(test_class)


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
        print(safe_dump(generate_test_input(test_class)))
