"""
ANTA catalog builder
"""
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

TestTuple = Tuple[str, Dict[str, str]]
Catalog = Dict[str, List[Dict[str, Any]]]

AVD_MAPPING: Dict[str, List[TestTuple]] = {
    "management_api_http": [("anta.tests.security.VerifyAPIHttpStatus", {}), ("anta.tests.security.VerifyAPIHttpsSSL", {"profile": "https_ssl_profile"})]
}


class CatalogBuilder(BaseModel):
    """
    CatalogBuilder is used to build and merge test catalogs from an AVD structured configuration.

    Attributes:
        structured_config: A dictionary representing the AVD structured config data.
        test_mapping: A dictionary mapping keys from the AVD structured config to ANTA tests.
        existing_catalog: An dictionary representing an existing ANTA test catalog. Defaults to an empty dictionary.
    """

    structured_config: Dict[str, Any]
    existing_catalog: Optional[Dict[str, List[Dict[str, Any]]]] = {}

    test_mapping = AVD_MAPPING

    @staticmethod
    def _get_package_name(test_name: str) -> str:
        """Extracts the package name from a fully qualified test name."""
        return test_name.rsplit(".", 1)[0]

    @staticmethod
    def _get_test_name(test_name: str) -> str:
        """Extracts the test name from a fully qualified test name."""
        return test_name.rsplit(".", 1)[1]

    @staticmethod
    def _update_test_parameters(value: Any, test_parameters: Dict[str, str]) -> Dict[str, Any]:
        """Updates the test parameters based on the provided structured configuration values."""
        return {param_key: value.get(structured_config_key) for param_key, structured_config_key in test_parameters.items()}

    def build_new_catalog(self) -> Catalog:
        """
        Constructs package tests from the structured configuration and the test mapping.

        Returns:
            A dictionary containing package tests.
        """
        package_tests: Catalog = {}
        for key, value in self.structured_config.items():
            if key in self.test_mapping:
                for test in self.test_mapping[key]:
                    full_test_name, test_parameters = test
                    package_name = self._get_package_name(full_test_name)
                    test_name = self._get_test_name(full_test_name)
                    test_parameters_updated = self._update_test_parameters(value, test_parameters)
                    if package_name not in package_tests:
                        package_tests[package_name] = []
                    package_tests[package_name].append({test_name: test_parameters_updated})
        return package_tests

    def merge_catalogs(self, new_catalog: Catalog) -> Catalog:
        """
        Merges the new catalog with the existing catalog, overwriting existing tests in the process.

        Args:
            new_catalog: A dictionary representing the new test catalog.

        Returns:
            A dictionary representing the merged catalog.
        """
        if not self.existing_catalog:
            return new_catalog

        for package, tests in new_catalog.items():
            if package in self.existing_catalog:
                for new_test in tests:
                    new_test_name, _ = list(new_test.items())[0]
                    self.existing_catalog[package] = [test for test in self.existing_catalog[package] if list(test.keys())[0] != new_test_name]
                    self.existing_catalog[package].append(new_test)
            else:
                self.existing_catalog[package] = tests
        return self.existing_catalog
