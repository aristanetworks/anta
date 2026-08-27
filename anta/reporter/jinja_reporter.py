# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Jinja report management for ANTA."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jinja2 import Template

if TYPE_CHECKING:
    import pathlib


class ReportJinja:  # pylint: disable=too-few-public-methods
    """Report builder based on a Jinja2 template."""

    def __init__(self, template_path: pathlib.Path) -> None:
        """Create a ReportJinja instance."""
        if not template_path.is_file():
            msg = f"template file is not found: {template_path}"
            raise FileNotFoundError(msg)

        self.template_path = template_path

    def render(self, data: list[dict[str, Any]], *, trim_blocks: bool = True, lstrip_blocks: bool = True) -> str:
        """Build a report based on a Jinja2 template.

        Report is built based on a J2 template provided by user.
        Data structure sent to template is:

        Example
        -------
        ```
        >>> print(ResultManager.json)
        [
            {
                name: ...,
                test: ...,
                result: ...,
                messages: [...]
                categories: ...,
                description: ...,
            }
        ]
        ```

        Parameters
        ----------
        data
            List of results from `ResultManager.results`.
        trim_blocks
            enable trim_blocks for J2 rendering.
        lstrip_blocks
            enable lstrip_blocks for J2 rendering.

        Returns
        -------
        str
            Rendered template

        """
        with self.template_path.open(encoding="utf-8") as file_:
            template = Template(file_.read(), trim_blocks=trim_blocks, lstrip_blocks=lstrip_blocks)

        return template.render({"data": data})
