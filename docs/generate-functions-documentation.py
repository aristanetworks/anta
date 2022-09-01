##!/usr/bin/python
# coding: utf-8 -*-

"""
This script uses the docstrings to generate the functions documentation in markdown format.
The generated markdown documentation is in the directory "documentation".
"""

import os
import sys
import shutil
from lazydocs import generate_docs

DOCUMENTATION_FOLDER = "./docs/api/"

if __name__ == "__main__":

    for filename in os.listdir(DOCUMENTATION_FOLDER):
        file_path = os.path.join(DOCUMENTATION_FOLDER, filename)
        print(f"Deleting {file_path}")
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:  # pylint: disable=broad-except
            print(f"! Failed to delete {file_path}. Reason: {e}")
            sys.exit(1)

    generate_docs(
        ["anta"],
        output_path=DOCUMENTATION_FOLDER,
        overview_file="README.md",
    )

    sys.exit(0)
