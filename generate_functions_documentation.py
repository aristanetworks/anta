"""
The functions to test EOS devices are coded in the module "functions" in the package "tests_eos"
These functions have docstrings.
This script uses the docstrings to generate the functions documentation in markdown format.
The generated markdown documentation is in the directory "documentation".
"""

from lazydocs import generate_docs

generate_docs(["tests_eos.functions"], output_path="./documentation", overview_file = 'overview.md')
