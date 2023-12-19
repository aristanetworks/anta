# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
import ast

from griffe import Class, Extension, ObjectNode, get_logger

logger = get_logger(__name__)

mkdocstrings_namespace = "mkdocstrings"


class AntaTestExtension(Extension):
    # Keeping this if I need input
    # def __init__(self, object_paths: list[str] | None = None) -> None:
    #    self.object_paths = object_paths

    def on_class_instance(self, node: ast.AST | ObjectNode, cls: Class) -> None:
        if isinstance(node, ObjectNode):
            return  # skip runtime objects, their docstrings are already right

        # need isinstance otherwise capturing Input as well
        if "AntaTest" in [base.id for base in node.bases if isinstance(base, ast.Name)]:
            logger.info(node.name)
            cls.extra[mkdocstrings_namespace]["template"] = "anta_test.html"

        # try:
        #    runtime_obj = dynamic_import(obj.path)
        #    if isinstance(runtime_obj, AntaTest):

        # except ImportError:
        #    logger.debug(f"Could not get dynamic docstring for {obj.path}")
        #    return

        # Maybe do extra stuff here
        # update the object instance with the evaluated docstring
        # docstring = inspect.cleandoc(docstring)
        # if obj.docstring:
        #    obj.docstring.value = docstring
        # else:
        #    obj.docstring = Docstring(docstring, parent=obj)
