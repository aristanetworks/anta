# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Script hooks.py to help mkdocstring python build documentation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import griffe
import yaml
from griffe import Class, Extension, ObjectNode
from griffe.docstrings.dataclasses import DocstringSectionKind

from anta.tests import aaa, configuration, connectivity, field_notices, hardware, interfaces, mlag, multicast, profiles, security, snmp, software, stp, system, vxlan
from anta.tests.routing import bgp, generic, ospf

if TYPE_CHECKING:
    import ast
    from types import ModuleType

LOGGER = logging.getLogger(__name__)


# ninjutsu - https://stackoverflow.com/questions/37200150/can-i-dump-blank-instead-of-null-in-yaml-pyyaml
def represent_none(self: yaml.representer.BaseRepresenter, _: Any) -> yaml.nodes.ScalarNode:
    # Accept Any
    # ruff: noqa: ANN401
    """Overewrite default representation of None from null to empty string."""
    return self.represent_scalar("tag:yaml.org,2002:null", "")


yaml.representer.SafeRepresenter.add_representer(type(None), represent_none)


def generate_test_input(test_class: Class) -> str:
    r"""Take a Griffe class and returm a string that represent a test input read from the docstring.

    When a single DocstringSectionKind.examples section is found in the docstring of the Inputs class,
    the parsing looks like (there be black voodoo magic):
        {'kind': 'examples',
         'value': [(<DocstringSectionKind.text: 'text'>,
                    'anta.tests.aaa:\n'
                    '    - VerifyAuthenMethods:\n'
                    '      methods:\n'
                    '        - local\n'
                    '        - none\n'
                    '        - logging\n'
                    '      types:\n'
                    '        - login\n'
                    '        - enable\n'
                    '        - dot1x')]}
    so need to retrieve the unique value (for now, and then the string in tuple)

    Args:
    ----
       test_class (griffe.Class): The AntaTest class griffe representation to generate inputs for.

    """
    try:
        # Dear future self, or someone else, I apologize, Parsing is weak in this piece of code.
        # But you know, this is for documentation so it probably breaks every 17 months and someone
        # needs to understand everything all over again. And who knows, there may be a better solution now?
        # May the parsing fun be with you.
        test_input = test_class.get_member("Input")
        parsed_docstring = test_input.docstring.parse(parser="numpy")
        examples = [section for section in parsed_docstring if section.kind == DocstringSectionKind.examples]
        if len(examples) == 1:
            example = examples[0]
            return yaml.safe_dump(yaml.safe_load(example.value[0][1]))

        if len(examples) > 1:
            inputs = f"TODO: Multiple examples section found in {test_class.name}.Input docstring, expecting only one."
            LOGGER.debug(inputs)
        else:
            inputs = f"TODO: add an example in {test_class.name}.Input docstring."
            LOGGER.debug(inputs)
    except KeyError:
        # no Input class
        inputs = None

    return yaml.safe_dump({test_class.parent.path: [{test_class.name: inputs}]})


def find_tests(module: ModuleType) -> list[Class]:
    """Probably can do fancy filtering."""
    griffe_module = griffe.load(module.__name__)
    griffe_classes = [griffe_module.get_member(class_name) for class_name in griffe_module.classes]
    return [griffe_class for griffe_class in griffe_classes if "AntaTest" in [base.name for base in griffe_class.bases]]


class GenerateInput(Extension):
    """Extension for Griffe to add an extra argument to AntaTest Class parsed for documentation.

    The extra argument is called anta_input.
    """

    # TODO: maybe an even better technique is simply to append the docstring Example from Input to the main docstring
    def on_class_instance(self, node: ast.AST | ObjectNode, cls: griffe.dataclasses.Class) -> None:
        """Add an anta_input attribute on classes during Griffe parsing is they are subclasses of AntaTest."""
        # Somehow pylint is crashing on this overriding.. complaining about 3 args vs 3 args
        # pylint: disable=arguments-differ
        # Only for subclass of AntaTest
        if "AntaTest" in [base.id for base in node.bases if hasattr(base, "id")]:
            LOGGER.debug("Generating input for %s", cls.path)
            griffe_module = griffe.load(cls.module.path)
            test_class = griffe_module.get_member(cls.name)
            cls.anta_input = generate_test_input(test_class)
            LOGGER.debug("Example input for %s:\n%s", test_class, cls.anta_input)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
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
    LOGGER.warning(all_test_classes)

    for _test_class in all_test_classes:
        LOGGER.warning(generate_test_input(_test_class))
