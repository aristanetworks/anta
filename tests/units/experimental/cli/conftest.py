# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Reuse the CLI runner and device mocks for experimental commands."""

from tests.units.cli.conftest import click_runner

__all__ = ["click_runner"]
