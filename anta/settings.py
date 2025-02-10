# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Settings for ANTA."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from httpx import Limits, Timeout
from pydantic import Field, NonNegativeFloat, NonNegativeInt, PositiveInt, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Default values for HTTPX resource limits
DEFAULT_HTTPX_MAX_CONNECTIONS = 10
DEFAULT_HTTPX_MAX_KEEPALIVE_CONNECTIONS = 10
DEFAULT_HTTPX_KEEPALIVE_EXPIRY = 5.0

# Default values for HTTPX timeouts
DEFAULT_HTTPX_CONNECT_TIMEOUT = 30.0
DEFAULT_HTTPX_READ_TIMEOUT = 30.0
DEFAULT_HTTPX_WRITE_TIMEOUT = 30.0
DEFAULT_HTTPX_POOL_TIMEOUT = None

# Default value for the maximum number of concurrent tests in the event loop
DEFAULT_MAX_CONCURRENCY = 10000

# Default value for the maximum number of open file descriptors for the ANTA process
DEFAULT_NOFILE = 16384


class FileDescriptorSettings(BaseSettings):
    """Environment variable for configuring the maximum number of open file descriptors for the ANTA process.

    On POSIX systems, this value is used to set the soft limit for the current process.
    The value cannot exceed the system's hard limit.

    Attributes
    ----------
    nofile : PositiveInt
        Environment variable: ANTA_NOFILE

        The maximum number of open file descriptors for the ANTA process. Defaults to 16384.
    """

    model_config = SettingsConfigDict(env_prefix="ANTA_")

    nofile: PositiveInt = Field(default=DEFAULT_NOFILE)


class MaxConcurrencySettings(BaseSettings):
    """Environment variable for configuring the maximum number of concurrent tests in the event loop.

    Attributes
    ----------
    max_concurrency : PositiveInt
        Environment variable: ANTA_MAX_CONCURRENCY

        The maximum number of concurrent tests that can run in the event loop. Defaults to 10000.
    """

    model_config = SettingsConfigDict(env_prefix="ANTA_")

    max_concurrency: PositiveInt = Field(default=DEFAULT_MAX_CONCURRENCY)


class HttpxResourceLimitsSettings(BaseSettings):
    """Environment variables for configuring the underlying HTTPX client resource limits.

    Attributes
    ----------
    max_connections : NonNegativeInt | None
        Environment variable: ANTA_MAX_CONNECTIONS

        Maximum number of allowable connections. Defaults to 10.

    max_keepalive_connections : NonNegativeInt | None
        Environment variable: ANTA_MAX_KEEPALIVE_CONNECTIONS

        Number of allowable keep-alive connections. Defaults to 10.

    keepalive_expiry : NonNegativeFloat | None
        Environment variable: ANTA_KEEPALIVE_EXPIRY

        Time limit on idle keep-alive connections in seconds. Defaults to 5.0.

    Notes
    -----
      Limits values can be set to `inf` to disable the limit for the given operation.
      `inf` gets converted to `None` when the settings are loaded.

      For more information on HTTPX resource limits, see: https://www.python-httpx.org/advanced/resource-limits/
    """

    # Prefix for environment variables
    model_config = SettingsConfigDict(env_prefix="ANTA_")

    max_connections: NonNegativeInt | None = Field(default=DEFAULT_HTTPX_MAX_CONNECTIONS)
    max_keepalive_connections: NonNegativeInt | None = Field(default=DEFAULT_HTTPX_MAX_KEEPALIVE_CONNECTIONS)
    keepalive_expiry: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_KEEPALIVE_EXPIRY)

    @field_validator("max_connections", "max_keepalive_connections", "keepalive_expiry", mode="before")
    @classmethod
    def convert_inf(cls, value: Any) -> Any:  # noqa: ANN401
        """Convert the value to `None` if it is equal to `inf`."""
        if value == "inf":
            return None
        return value


class HttpxTimeoutsSettings(BaseSettings):
    """Environment variables for configuring the underlying HTTPX client timeouts.

    Attributes
    ----------
    connect_timeout : NonNegativeFloat | None
        Environment variable: ANTA_CONNECT_TIMEOUT

        Maximum amount of time to wait until a socket connection to the requested host is established. Defaults to 30.0.

    read_timeout : NonNegativeFloat | None
        Environment variable: ANTA_READ_TIMEOUT

        Maximum duration to wait for a chunk of data to be received (for example, a chunk of the response body). Defaults to 30.0.

    write_timeout : NonNegativeFloat | None
        Environment variable: ANTA_WRITE_TIMEOUT

        Maximum duration to wait for a chunk of data to be sent (for example, a chunk of the request body). Defaults to 30.0.

    pool_timeout : NonNegativeFloat | None
        Environment variable: ANTA_POOL_TIMEOUT

        Maximum duration to wait for acquiring a connection from the connection pool. Defaults to None (no timeout).

    Notes
    -----
      Timeouts values can be set to `inf` to disable the timeout for the given operation.
      `inf` gets converted to `None` when the settings are loaded.

      For more information on HTTPX timeouts, see: https://www.python-httpx.org/advanced/timeouts/
    """

    # Prefix for environment variables
    model_config = SettingsConfigDict(env_prefix="ANTA_")

    connect_timeout: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_CONNECT_TIMEOUT)
    read_timeout: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_READ_TIMEOUT)
    write_timeout: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_WRITE_TIMEOUT)
    pool_timeout: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_POOL_TIMEOUT)

    @field_validator("connect_timeout", "read_timeout", "write_timeout", "pool_timeout", mode="before")
    @classmethod
    def convert_inf(cls, value: Any) -> Any:  # noqa: ANN401
        """Convert the value to `None` if it is equal to `inf`."""
        if value == "inf":
            return None
        return value


def get_max_concurrency() -> int:
    """Get the maximum number of concurrent tests that can run in the event loop from environment variables.

    Returns
    -------
    int
        The maximum number of concurrent tests that can run in the event loop.
    """
    settings = MaxConcurrencySettings()
    return settings.max_concurrency


def get_httpx_limits() -> Limits:
    """Get the HTTPX Limits object from environment variables.

    Returns
    -------
    Limits
        The HTTPX Limits object with the specified limit values.
    """
    settings = HttpxResourceLimitsSettings()
    return Limits(
        max_connections=settings.max_connections,
        max_keepalive_connections=settings.max_keepalive_connections,
        keepalive_expiry=settings.keepalive_expiry,
    )


def get_httpx_timeout(timeout: float | None = None) -> Timeout:
    """Get the HTTPX Timeout object from environment variables or the provided timeout value.

    Parameters
    ----------
    timeout : float, optional
        When provided, this value is used for all timeouts. `float("inf")` is supported to disable all timeouts.

    Returns
    -------
    Timeout
        The HTTPX Timeout object with the specified timeout values.
    """
    # If timeout is set to float("inf"), disable all timeouts
    if timeout == float("inf"):
        return Timeout(timeout=None)

    # If timeout is provided, we use that value for all timeouts
    if timeout is not None:
        return Timeout(timeout=timeout)

    # If timeout is None, no timeout was provided so we load and use the environment variables or defaults
    settings = HttpxTimeoutsSettings()
    return Timeout(
        connect=settings.connect_timeout,
        read=settings.read_timeout,
        write=settings.write_timeout,
        pool=settings.pool_timeout,
    )


def get_file_descriptor_limit() -> int:
    """Get the file descriptor limit for the current ANTA process.

    On POSIX systems, adjusts the process's soft limit based on ANTA_NOFILE environment
    variable while respecting the system's hard limit, meaning the new soft limit cannot
    exceed the system's hard limit.

    On non-POSIX systems, returns `sys.maxsize` as the limit.

    Returns
    -------
    int
        The maximum number of file descriptors available to the process.
    """
    if os.name != "posix":
        logger.warning("Running on a non-POSIX system, cannot adjust the maximum number of file descriptors.")
        return sys.maxsize

    import resource

    settings = FileDescriptorSettings()
    limits = resource.getrlimit(resource.RLIMIT_NOFILE)
    logger.debug("Initial file descriptor limits: Soft Limit: %s | Hard Limit: %s", limits[0], limits[1])

    # Set new soft limit to minimum of requested and hard limit
    new_soft_limit = min(limits[1], settings.nofile)
    logger.debug("Setting file descriptor soft limit to %s", new_soft_limit)
    resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft_limit, limits[1]))

    return resource.getrlimit(resource.RLIMIT_NOFILE)[0]
