# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Settings for ANTA."""

from __future__ import annotations

import logging
import os
import sys

from pydantic import Field, PositiveInt, PrivateAttr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from anta.logger import exc_to_str

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENCY = 50000
"""Default value for the maximum number of concurrent tests in the event loop."""

DEFAULT_NOFILE = 16384
"""Default value for the maximum number of open file descriptors for the ANTA process."""


class AntaRunnerSettings(BaseSettings):
    """Environment variables for configuring the ANTA runner.

    When initialized, relevant environment variables are loaded. If not set, default values are used.

    On POSIX systems, also adjusts the process soft limit based on the `ANTA_NOFILE` environment variable
    while respecting the system hard limit, meaning the new soft limit cannot exceed the system's hard limit.

    On non-POSIX systems (Windows), sets the limit to `sys.maxsize`.

    The adjusted limit is available with the `file_descriptor_limit` property after initialization.

    Attributes
    ----------
    nofile : PositiveInt
        Environment variable: ANTA_NOFILE

        The maximum number of open file descriptors for the ANTA process. Defaults to 16384.

    max_concurrency : PositiveInt
        Environment variable: ANTA_MAX_CONCURRENCY

        The maximum number of concurrent tests that can run in the event loop. Defaults to 50000.
    """

    model_config = SettingsConfigDict(env_prefix="ANTA_")

    nofile: PositiveInt = Field(default=DEFAULT_NOFILE)
    max_concurrency: PositiveInt = Field(default=DEFAULT_MAX_CONCURRENCY)

    _file_descriptor_limit: PositiveInt = PrivateAttr()

    @model_validator(mode="after")
    def set_and_compute_file_descriptor_limit(self) -> AntaRunnerSettings:
        """Execute the system call to set the file descriptor limit and computes the effective limit."""
        calculated_limit: int

        if os.name != "posix":
            logger.warning("Running on a non-POSIX system, cannot adjust the maximum number of file descriptors.")
            calculated_limit = sys.maxsize
        else:
            import resource  # noqa: PLC0415

            limits = resource.getrlimit(resource.RLIMIT_NOFILE)
            logger.debug("Initial file descriptor limits for the current ANTA process: Soft Limit: %s | Hard Limit: %s", limits[0], limits[1])

            # Set new soft limit to minimum of requested and hard limit
            new_soft_limit = min(limits[1], self.nofile)
            logger.debug("Setting file descriptor soft limit to %s", new_soft_limit)

            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft_limit, limits[1]))
            except ValueError as exception:
                logger.warning("Failed to set file descriptor soft limit for the current ANTA process: %s", exc_to_str(exception))

            calculated_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]

        self._file_descriptor_limit = calculated_limit
        return self

    @property
    def file_descriptor_limit(self) -> PositiveInt:
        """The maximum number of file descriptors available to the process."""
        return self._file_descriptor_limit
