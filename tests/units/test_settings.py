# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the anta.settings module."""

from __future__ import annotations

import logging
import os
import sys
from unittest.mock import patch

import pytest
from httpx import Limits, Timeout
from pydantic import ValidationError

from anta.settings import (
    DEFAULT_HTTPX_CONNECT_TIMEOUT,
    DEFAULT_HTTPX_KEEPALIVE_EXPIRY,
    DEFAULT_HTTPX_MAX_CONNECTIONS,
    DEFAULT_HTTPX_MAX_KEEPALIVE_CONNECTIONS,
    DEFAULT_HTTPX_POOL_TIMEOUT,
    DEFAULT_HTTPX_READ_TIMEOUT,
    DEFAULT_HTTPX_WRITE_TIMEOUT,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_NOFILE,
    FileDescriptorSettings,
    HttpxResourceLimitsSettings,
    HttpxTimeoutsSettings,
    MaxConcurrencySettings,
    get_file_descriptor_limit,
    get_httpx_limits,
    get_httpx_timeout,
    get_max_concurrency,
)

if os.name == "posix":
    # The function is not defined on non-POSIX system
    import resource


class TestFileDescriptor:
    """Tests for the FileDescriptiorSettings class."""

    def test_default(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test default file descriptor value."""
        settings = FileDescriptorSettings()
        assert settings.nofile == DEFAULT_NOFILE

    def test_env_var(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test setting file descriptor limit via environment variable."""
        setenvvar.setenv("ANTA_NOFILE", "20480")
        settings = FileDescriptorSettings()
        assert settings.nofile == 20480

    def test_validation(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test validation of file descriptor value."""
        setenvvar.setenv("ANTA_NOFILE", "-1")
        with pytest.raises(ValidationError):
            FileDescriptorSettings()

        setenvvar.setenv("ANTA_NOFILE", "0")
        with pytest.raises(ValidationError):
            FileDescriptorSettings()

        setenvvar.setenv("ANTA_NOFILE", "unlimited")
        with pytest.raises(ValidationError):
            FileDescriptorSettings()


class TestMaxConcurrency:
    """Tests for the MaxConcurrencySettings class."""

    def test_default(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test default max concurrency value."""
        settings = MaxConcurrencySettings()
        assert settings.max_concurrency == DEFAULT_MAX_CONCURRENCY

    def test_env_var(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test setting max concurrency via environment variable."""
        setenvvar.setenv("ANTA_MAX_CONCURRENCY", "500")
        assert get_max_concurrency() == 500

    def test_validation(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test validation of max concurrency value."""
        setenvvar.setenv("ANTA_MAX_CONCURRENCY", "-1")
        with pytest.raises(ValidationError):
            MaxConcurrencySettings()

        setenvvar.setenv("ANTA_MAX_CONCURRENCY", "0")
        with pytest.raises(ValidationError):
            MaxConcurrencySettings()

        setenvvar.setenv("ANTA_MAX_CONCURRENCY", "Unlimited")
        with pytest.raises(ValidationError):
            MaxConcurrencySettings()


class TestHttpxLimits:
    """Tests for the HttpxResourceLimitsSettings class."""

    def test_default(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test default HTTPX limits."""
        settings = HttpxResourceLimitsSettings()
        assert settings.max_connections == DEFAULT_HTTPX_MAX_CONNECTIONS
        assert settings.max_keepalive_connections == DEFAULT_HTTPX_MAX_KEEPALIVE_CONNECTIONS
        assert settings.keepalive_expiry == DEFAULT_HTTPX_KEEPALIVE_EXPIRY

    def test_env_vars(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test setting HTTPX limits via environment variables."""
        setenvvar.setenv("ANTA_MAX_CONNECTIONS", "200")
        setenvvar.setenv("ANTA_MAX_KEEPALIVE_CONNECTIONS", "40")
        setenvvar.setenv("ANTA_KEEPALIVE_EXPIRY", "10.0")

        limits = get_httpx_limits()
        assert isinstance(limits, Limits)
        assert limits.max_connections == 200
        assert limits.max_keepalive_connections == 40
        assert limits.keepalive_expiry == 10.0

    def test_none_values(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test setting HTTPX limits to None via environment variables."""
        setenvvar.setenv("ANTA_MAX_CONNECTIONS", "None")
        setenvvar.setenv("ANTA_MAX_KEEPALIVE_CONNECTIONS", "None")
        setenvvar.setenv("ANTA_KEEPALIVE_EXPIRY", "None")

        limits = get_httpx_limits()
        assert limits.max_connections is None
        assert limits.max_keepalive_connections is None
        assert limits.keepalive_expiry is None

    def test_mixed_values(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test mixing None and numeric values."""
        setenvvar.setenv("ANTA_MAX_CONNECTIONS", "None")
        setenvvar.setenv("ANTA_MAX_KEEPALIVE_CONNECTIONS", "50")
        setenvvar.setenv("ANTA_KEEPALIVE_EXPIRY", "15.0")

        limits = get_httpx_limits()
        assert limits.max_connections is None
        assert limits.max_keepalive_connections == 50
        assert limits.keepalive_expiry == 15.0

    def test_httpx_limits_validation(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test validation of HTTPX resource limits values."""
        # Test negative values
        setenvvar.setenv("ANTA_MAX_CONNECTIONS", "-1")
        with pytest.raises(ValidationError):
            HttpxResourceLimitsSettings()

        setenvvar.setenv("ANTA_MAX_KEEPALIVE_CONNECTIONS", "-5")
        with pytest.raises(ValidationError):
            HttpxResourceLimitsSettings()

        setenvvar.setenv("ANTA_KEEPALIVE_EXPIRY", "-2.5")
        with pytest.raises(ValidationError):
            HttpxResourceLimitsSettings()

        # Test invalid string values
        setenvvar.setenv("ANTA_MAX_CONNECTIONS", "unlimited")
        with pytest.raises(ValidationError):
            HttpxResourceLimitsSettings()

        setenvvar.setenv("ANTA_MAX_KEEPALIVE_CONNECTIONS", "infinity")
        with pytest.raises(ValidationError):
            HttpxResourceLimitsSettings()

        setenvvar.setenv("ANTA_KEEPALIVE_EXPIRY", "forever")
        with pytest.raises(ValidationError):
            HttpxResourceLimitsSettings()

        # Test zero values (should be valid for NonNegative types)
        setenvvar.setenv("ANTA_MAX_CONNECTIONS", "0")
        setenvvar.setenv("ANTA_MAX_KEEPALIVE_CONNECTIONS", "0")
        setenvvar.setenv("ANTA_KEEPALIVE_EXPIRY", "0.0")
        settings = HttpxResourceLimitsSettings()
        assert settings.max_connections == 0
        assert settings.max_keepalive_connections == 0
        assert settings.keepalive_expiry == 0.0


class TestHttpxTimeouts:
    """Tests for the HttpxTimeoutsSettings class."""

    def test_default(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test default HTTPX timeout values."""
        settings = HttpxTimeoutsSettings()
        assert settings.connect_timeout == DEFAULT_HTTPX_CONNECT_TIMEOUT
        assert settings.read_timeout == DEFAULT_HTTPX_READ_TIMEOUT
        assert settings.write_timeout == DEFAULT_HTTPX_WRITE_TIMEOUT
        assert settings.pool_timeout == DEFAULT_HTTPX_POOL_TIMEOUT

    def test_env_vars(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test setting HTTPX timeouts via environment variables."""
        setenvvar.setenv("ANTA_CONNECT_TIMEOUT", "10.0")
        setenvvar.setenv("ANTA_READ_TIMEOUT", "15.0")
        setenvvar.setenv("ANTA_WRITE_TIMEOUT", "20.0")
        setenvvar.setenv("ANTA_POOL_TIMEOUT", "25.0")

        timeout = get_httpx_timeout(default_timeout=30.0)
        assert isinstance(timeout, Timeout)
        assert timeout.connect == 10.0
        assert timeout.read == 15.0
        assert timeout.write == 20.0
        assert timeout.pool == 25.0

    def test_none_values(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test setting HTTPX timeouts to None (no timeout) via environment variables."""
        setenvvar.setenv("ANTA_CONNECT_TIMEOUT", "None")
        setenvvar.setenv("ANTA_READ_TIMEOUT", "None")
        setenvvar.setenv("ANTA_WRITE_TIMEOUT", "None")
        setenvvar.setenv("ANTA_POOL_TIMEOUT", "None")

        timeout = get_httpx_timeout(default_timeout=30.0)
        assert timeout.connect is None
        assert timeout.read is None
        assert timeout.write is None
        assert timeout.pool is None

    def test_property_flags(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test the timeout property flags that indicate if values were set by environment variables."""
        settings = HttpxTimeoutsSettings()
        assert not settings.connect_set
        assert not settings.read_set
        assert not settings.write_set
        assert not settings.pool_set

        setenvvar.setenv("ANTA_CONNECT_TIMEOUT", "None")
        setenvvar.setenv("ANTA_READ_TIMEOUT", "15.0")
        settings = HttpxTimeoutsSettings()
        assert settings.connect_set
        assert settings.read_set
        assert not settings.write_set
        assert not settings.pool_set

    def test_timeout_with_default_none(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test behavior when default_timeout is None."""
        timeout = get_httpx_timeout(default_timeout=None)
        assert timeout.connect is None
        assert timeout.read is None
        assert timeout.write is None
        assert timeout.pool is None

    def test_mixed_timeouts(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test mixing different timeout configurations."""
        setenvvar.setenv("ANTA_CONNECT_TIMEOUT", "5.0")
        setenvvar.setenv("ANTA_READ_TIMEOUT", "None")

        timeout = get_httpx_timeout(default_timeout=10.0)
        assert timeout.connect == 5.0
        assert timeout.read is None
        assert timeout.write == 10.0
        assert timeout.pool == 10.0

    def test_httpx_timeouts_validation(self, setenvvar: pytest.MonkeyPatch) -> None:
        """Test validation of HTTPX timeout values."""
        # Test negative values
        setenvvar.setenv("ANTA_CONNECT_TIMEOUT", "-1.0")
        with pytest.raises(ValidationError):
            HttpxTimeoutsSettings()

        setenvvar.setenv("ANTA_READ_TIMEOUT", "-5.0")
        with pytest.raises(ValidationError):
            HttpxTimeoutsSettings()

        setenvvar.setenv("ANTA_WRITE_TIMEOUT", "-2.5")
        with pytest.raises(ValidationError):
            HttpxTimeoutsSettings()

        setenvvar.setenv("ANTA_POOL_TIMEOUT", "-3.0")
        with pytest.raises(ValidationError):
            HttpxTimeoutsSettings()

        # Test invalid string values
        setenvvar.setenv("ANTA_CONNECT_TIMEOUT", "instant")
        with pytest.raises(ValidationError):
            HttpxTimeoutsSettings()

        setenvvar.setenv("ANTA_READ_TIMEOUT", "forever")
        with pytest.raises(ValidationError):
            HttpxTimeoutsSettings()

        setenvvar.setenv("ANTA_WRITE_TIMEOUT", "unlimited")
        with pytest.raises(ValidationError):
            HttpxTimeoutsSettings()

        setenvvar.setenv("ANTA_POOL_TIMEOUT", "infinite")
        with pytest.raises(ValidationError):
            HttpxTimeoutsSettings()

        # Test zero values (should be valid for NonNegative types)
        setenvvar.setenv("ANTA_CONNECT_TIMEOUT", "0.0")
        setenvvar.setenv("ANTA_READ_TIMEOUT", "0.0")
        setenvvar.setenv("ANTA_WRITE_TIMEOUT", "0.0")
        setenvvar.setenv("ANTA_POOL_TIMEOUT", "0.0")
        settings = HttpxTimeoutsSettings()
        assert settings.connect_timeout == 0.0
        assert settings.read_timeout == 0.0
        assert settings.write_timeout == 0.0
        assert settings.pool_timeout == 0.0


@pytest.mark.skipif(os.name != "posix", reason="Cannot run this test on Windows")
def test_get_file_descriptor_limit(caplog: pytest.LogCaptureFixture) -> None:
    """Test get_file_descriptor_limit on POSIX systems."""
    with (
        caplog.at_level(logging.DEBUG),
        patch.dict("os.environ", {"ANTA_NOFILE": "20480"}),
        patch("resource.getrlimit") as getrlimit_mock,
        patch("resource.setrlimit") as setrlimit_mock,
    ):
        # Simulate the default system limits
        system_limits = (8192, 1048576)

        # Setup getrlimit mock return value
        getrlimit_mock.return_value = system_limits

        # Simulate setrlimit behavior
        def side_effect_setrlimit(resource_id: int, limits: tuple[int, int]) -> None:
            _ = resource_id
            getrlimit_mock.return_value = (limits[0], limits[1])

        setrlimit_mock.side_effect = side_effect_setrlimit

        result = get_file_descriptor_limit()

        # Assert the limits were updated as expected
        assert result == 20480
        assert "Initial file descriptor limits: Soft Limit: 8192 | Hard Limit: 1048576" in caplog.text
        assert "Setting file descriptor soft limit to 20480" in caplog.text

        setrlimit_mock.assert_called_once_with(resource.RLIMIT_NOFILE, (20480, 1048576))  # pylint: disable=possibly-used-before-assignment


@pytest.mark.skipif(os.name == "posix", reason="Run this test on Windows only")
def test_get_file_descriptor_limit_windows(caplog: pytest.LogCaptureFixture) -> None:
    """Test get_file_descriptor_limit on Windows."""
    caplog.set_level(logging.INFO)
    result = get_file_descriptor_limit()
    assert result == sys.maxsize
    assert "Running on a non-POSIX system, cannot adjust the maximum number of file descriptors." in caplog.text
