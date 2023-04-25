"""
conftest.py
"""
from glob import glob
from pathlib import Path

CONFTEST_PARENT_DIR = f"{Path(__file__).parent}"


def refactor(string: str) -> str:
    """
    Replace the absolute path by 'tests'
    Then the various directory separators (windowx or linux) by '.'
    Finally remove the file extension
    """
    string = string.replace(CONFTEST_PARENT_DIR, "tests")
    return string.replace("/", ".").replace("\\", ".").replace(".py", "")


pytest_plugins = [refactor(fixture) for fixture in glob(f"{CONFTEST_PARENT_DIR}/lib/fixture.py") if "__" not in fixture]
