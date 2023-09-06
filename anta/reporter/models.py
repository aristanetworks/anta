# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models related to anta.result_manager module."""

from pydantic import BaseModel
from rich.text import Text

from anta.custom_types import TestStatus


class ColorManager(BaseModel):
    """Color management for status report.

    Attributes:
        level (str): Test result value.
        color (str): Associated color.
    """

    level: TestStatus
    color: str

    def style_rich(self) -> Text:
        """
        Build a rich Text syntax with color

        Returns:
            Text: object with level string and its associated color.
        """
        return Text(self.level, style=self.color)

    def string(self) -> str:
        """
        Build an str with color code

        Returns:
            str: String with level and its associated color
        """
        return f"[{self.color}]{self.level}"
