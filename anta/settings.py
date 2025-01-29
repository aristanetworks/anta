# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Settings for ANTA."""

from __future__ import annotations

import logging
import os
import sys

from httpx import Limits, Timeout
from pydantic import Field, NonNegativeFloat, NonNegativeInt, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Default values for HTTPX resource limits
DEFAULT_HTTPX_MAX_CONNECTIONS = 100
DEFAULT_HTTPX_MAX_KEEPALIVE_CONNECTIONS = 20
DEFAULT_HTTPX_KEEPALIVE_EXPIRY = 5.0

# Default values for HTTPX timeouts
DEFAULT_HTTPX_CONNECT_TIMEOUT = 5.0
DEFAULT_HTTPX_READ_TIMEOUT = 5.0
DEFAULT_HTTPX_WRITE_TIMEOUT = 5.0
DEFAULT_HTTPX_POOL_TIMEOUT = 5.0

# Default value for the maximum number of concurrent tests in the event loop
DEFAULT_MAX_CONCURRENCY = 10000

# Default value for the maximum number of open file descriptors for the ANTA process
DEFAULT_NOFILE = 16384


class FileDescriptorSettings(BaseSettings):
    """Environment variable for configuring the maximum number of open file descriptors for the ANTA process.

    On POSIX systems, this value is used to set the soft limit for the current process.
    The value cannot exceed the system's hard limit.
    """

    model_config = SettingsConfigDict(env_prefix="ANTA_")

    nofile: PositiveInt = Field(default=DEFAULT_NOFILE)


class MaxConcurrencySettings(BaseSettings):
    """Environment variable for configuring the maximum number of concurrent tests in the event loop."""

    model_config = SettingsConfigDict(env_prefix="ANTA_")

    max_concurrency: PositiveInt = Field(default=DEFAULT_MAX_CONCURRENCY)


class HttpxResourceLimitsSettings(BaseSettings):
    """Environment variables for configuring the underlying HTTPX client resource limits.

    The limits are set using the following environment variables:
        - ANTA_MAX_CONNECTIONS: Maximum number of allowable connections.
        - ANTA_MAX_KEEPALIVE_CONNECTIONS: Number of allowable keep-alive connections.
        - ANTA_KEEPALIVE_EXPIRY: Time limit on idle keep-alive connections in seconds.

    If any environment variable is not set, the following HTTPX default limits are used:
        - max_connections: 100
        - max_keepalive_connections: 20
        - keepalive_expiry: 5.0

    These limits are set for all devices. `None` means no limit is set for the given operation.

    For more information on HTTPX resource limits, see: https://www.python-httpx.org/advanced/resource-limits/
    """

    # The 'None' string is used to allow the environment variable to be set to `None`.
    model_config = SettingsConfigDict(env_parse_none_str="None", env_prefix="ANTA_")

    max_connections: NonNegativeInt | None = Field(default=DEFAULT_HTTPX_MAX_CONNECTIONS)
    max_keepalive_connections: NonNegativeInt | None = Field(default=DEFAULT_HTTPX_MAX_KEEPALIVE_CONNECTIONS)
    keepalive_expiry: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_KEEPALIVE_EXPIRY)


class HttpxTimeoutsSettings(BaseSettings):
    """Environment variables for configuring the underlying HTTPX client timeouts.

    The timeouts are set using the following environment variables:
        - ANTA_CONNECT_TIMEOUT: Maximum amount of time to wait until a socket connection to the requested host is established.
        - ANTA_READ_TIMEOUT: Maximum duration to wait for a chunk of data to be received (for example, a chunk of the response body).
        - ANTA_WRITE_TIMEOUT: Maximum duration to wait for a chunk of data to be sent (for example, a chunk of the request body).
        - ANTA_POOL_TIMEOUT: Maximum duration to wait for acquiring a connection from the connection pool.

    If any environment variable is not set, the default HTTPX timeout is used, 5 seconds.
    `None` will disable the timeout for the given operation.

    For more information on HTTPX timeouts, see: https://www.python-httpx.org/advanced/timeouts/
    """

    # The 'None' string is used to allow the environment variable to be set to `None`.
    model_config = SettingsConfigDict(env_parse_none_str="None", env_prefix="ANTA_")

    connect_timeout: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_CONNECT_TIMEOUT)
    read_timeout: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_READ_TIMEOUT)
    write_timeout: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_WRITE_TIMEOUT)
    pool_timeout: NonNegativeFloat | None = Field(default=DEFAULT_HTTPX_POOL_TIMEOUT)

    # The following properties are used to determine if a specific timeout was set by an environment variable
    @property
    def connect_set(self) -> bool:
        """Return True if the connect timeout was set by an environment variable."""
        return "connect_timeout" in self.model_fields_set

    @property
    def read_set(self) -> bool:
        """Return True if the read timeout was set by an environment variable."""
        return "read_timeout" in self.model_fields_set

    @property
    def write_set(self) -> bool:
        """Return True if the write timeout was set by an environment variable."""
        return "write_timeout" in self.model_fields_set

    @property
    def pool_set(self) -> bool:
        """Return True if the pool timeout was set by an environment variable."""
        return "pool_timeout" in self.model_fields_set


def get_max_concurrency() -> int:
    """Get the maximum number of concurrent tests that can run in the event loop."""
    settings = MaxConcurrencySettings()
    return settings.max_concurrency


def get_httpx_limits() -> Limits:
    """Get the HTTPX Limits object from environment variables."""
    settings = HttpxResourceLimitsSettings()
    return Limits(
        max_connections=settings.max_connections,
        max_keepalive_connections=settings.max_keepalive_connections,
        keepalive_expiry=settings.keepalive_expiry,
    )


def get_httpx_timeout(default_timeout: float | None) -> Timeout:
    """Get the HTTPX Timeout object from environment variables.

    Parameters
    ----------
    default_timeout : float | None
        Default timeout value to use if no specific timeout is set for a given operation.

    Notes
    -----
    When running ANTA NRFU from the command line, `default_timeout` is set to 30 seconds by default.
    Otherwise, by default, an `AsyncEOSDevice` class is instantiated with a `timeout` parameter set
    to `None`, meaning no timeout is set.
    """
    settings = HttpxTimeoutsSettings()
    return Timeout(
        connect=settings.connect_timeout if settings.connect_set else default_timeout,
        read=settings.read_timeout if settings.read_set else default_timeout,
        write=settings.write_timeout if settings.write_set else default_timeout,
        pool=settings.pool_timeout if settings.pool_set else default_timeout,
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
