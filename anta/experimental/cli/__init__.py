# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""CLI support for experimental ANTA features."""


def warn_experimental(feature: str) -> None:
    """Warn users when an experimental CLI feature is executed."""
    # The stable CLI registers experimental commands while its package is initializing.
    from anta.cli.console import console  # noqa: PLC0415

    console.print(
        f"WARNING: You are using an experimental ANTA feature: {feature}. Its API, behavior and output may change between releases.",
        style="yellow",
    )
