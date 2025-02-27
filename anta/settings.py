# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Settings for ANTA."""

from __future__ import annotations

import logging
import os
import sys
from enum import Enum
from typing import Any

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Default value for the maximum number of concurrent tests in the event loop
DEFAULT_MAX_CONCURRENCY = 10000

# Default value for the maximum number of open file descriptors for the ANTA process
DEFAULT_NOFILE = 16384

# Default value for the test scheduling strategy
DEFAULT_SCHEDULING_STRATEGY = "round-robin"

# Default value for the number of tests to schedule per device when using the DEVICE_BY_COUNT scheduling strategy
DEFAULT_SCHEDULING_TESTS_PER_DEVICE = 100


class AntaRunnerSchedulingStrategy(str, Enum):
    """Enum for the test scheduling strategies available in the ANTA runner.

    * ROUND_ROBIN: Distribute tests across devices in a round-robin fashion.
    * DEVICE_BY_DEVICE: Run all tests on a single device before moving to the next.
    * DEVICE_BY_COUNT: Run all tests on a single device for a specified count before moving to the next.

    NOTE: This could be updated to StrEnum when Python 3.11 is the minimum supported version in ANTA.
    """

    ROUND_ROBIN = "round-robin"
    DEVICE_BY_DEVICE = "device-by-device"
    DEVICE_BY_COUNT = "device-by-count"

    def __str__(self) -> str:
        """Override the __str__ method to return the value of the Enum, mimicking the behavior of StrEnum."""
        return self.value


class AntaRunnerSettings(BaseSettings):
    """Environment variables for configuring the ANTA runner.

    When initialized, relevant environment variables are loaded. If not set, default values are used.

    On POSIX systems, also adjusts the process's soft limit based on the `ANTA_NOFILE` environment variable
    while respecting the system's hard limit, meaning the new soft limit cannot exceed the system's hard limit.

    On non-POSIX systems (Windows), sets the limit to `sys.maxsize`.

    The adjusted limit is available with the `file_descriptor_limit` property after initialization.

    Attributes
    ----------
    nofile : PositiveInt
        Environment variable: ANTA_NOFILE

        The maximum number of open file descriptors for the ANTA process. Defaults to 16384.

    max_concurrency : PositiveInt
        Environment variable: ANTA_MAX_CONCURRENCY

        The maximum number of concurrent tests that can run in the event loop. Defaults to 10000.

    scheduling_strategy : AntaRunnerSchedulingStrategy
        Environment variable: ANTA_SCHEDULING_STRATEGY

        The test scheduling strategy to use when running tests. Defaults to "round-robin".

    scheduling_tests_per_device : PositiveInt
        Environment variable: ANTA_SCHEDULING_TESTS_PER_DEVICE

        The number of tests to schedule per device when using the `DEVICE_BY_COUNT` scheduling strategy. Defaults to 100.
    """

    model_config = SettingsConfigDict(env_prefix="ANTA_")

    nofile: PositiveInt = Field(default=DEFAULT_NOFILE)
    max_concurrency: PositiveInt = Field(default=DEFAULT_MAX_CONCURRENCY)
    scheduling_strategy: AntaRunnerSchedulingStrategy = Field(default=AntaRunnerSchedulingStrategy(DEFAULT_SCHEDULING_STRATEGY))
    scheduling_tests_per_device: PositiveInt = Field(default=DEFAULT_SCHEDULING_TESTS_PER_DEVICE)

    # Computed in post-init
    _file_descriptor_limit: PositiveInt

    def model_post_init(self, __context: Any) -> None:  # noqa: ANN401, PYI063
        """Post-initialization method to set the file descriptor limit for the current ANTA process."""
        if os.name != "posix":
            logger.warning("Running on a non-POSIX system, cannot adjust the maximum number of file descriptors.")
            self._file_descriptor_limit = sys.maxsize
            return

        import resource

        limits = resource.getrlimit(resource.RLIMIT_NOFILE)
        logger.debug("Initial file descriptor limits: Soft Limit: %s | Hard Limit: %s", limits[0], limits[1])

        # Set new soft limit to minimum of requested and hard limit
        new_soft_limit = min(limits[1], self.nofile)
        logger.debug("Setting file descriptor soft limit to %s", new_soft_limit)
        resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft_limit, limits[1]))

        self._file_descriptor_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        return

    @property
    def file_descriptor_limit(self) -> PositiveInt:
        """The maximum number of file descriptors available to the process."""
        return self._file_descriptor_limit
