# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from pathlib import Path


def get_templates_path() -> Path:
    return Path(__file__).parent / "templates"
