# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi._models module."""

from typing import TYPE_CHECKING
from uuid import UUID

import pytest

from asynceapi._constants import EapiCommandFormat
from asynceapi._errors import EapiReponseError
from asynceapi._models import EapiCommandResult, EapiRequest, EapiResponse

if TYPE_CHECKING:
    from asynceapi._types import EapiComplexCommand, EapiSimpleCommand


class TestEapiRequest:
    """Test cases for the EapiRequest class."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with just required parameters."""
        commands: list[EapiSimpleCommand | EapiComplexCommand] = ["show version", "show interfaces"]
        req = EapiRequest(commands=commands)

        # Check required attributes
        assert req.commands == commands

        # Check default values
        assert req.version == "latest"
        assert req.format == EapiCommandFormat.JSON
        assert req.timestamps is False
        assert req.auto_complete is False
        assert req.expand_aliases is False
        assert req.stop_on_error is True

        # Check that ID is generated as a UUID hex string
        try:
            UUID(str(req.id))
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        assert is_valid_uuid

    def test_init_with_custom_values(self) -> None:
        """Test initialization with custom parameter values."""
        commands: list[EapiSimpleCommand | EapiComplexCommand] = [{"cmd": "enable", "input": "password"}, "show version"]
        req = EapiRequest(
            commands=commands,
            version=1,
            format=EapiCommandFormat.TEXT,
            timestamps=True,
            auto_complete=True,
            expand_aliases=True,
            stop_on_error=False,
            id="custom-id-123",
        )

        # Check all attributes match expected values
        assert req.commands == commands
        assert req.version == 1
        assert req.format == EapiCommandFormat.TEXT
        assert req.timestamps is True
        assert req.auto_complete is True
        assert req.expand_aliases is True
        assert req.stop_on_error is False
        assert req.id == "custom-id-123"

    def test_to_jsonrpc(self) -> None:
        """Test conversion to JSON-RPC dictionary."""
        commands: list[EapiSimpleCommand | EapiComplexCommand] = ["show version", "show interfaces"]
        req = EapiRequest(commands=commands, version=1, format=EapiCommandFormat.TEXT, id="test-id-456")

        jsonrpc = req.to_jsonrpc()

        # Check that structure matches expected JSON-RPC format
        assert jsonrpc["jsonrpc"] == "2.0"
        assert jsonrpc["method"] == "runCmds"
        assert jsonrpc["id"] == "test-id-456"

        # Check params matches our configuration
        params = jsonrpc["params"]
        assert params["version"] == 1
        assert params["cmds"] == commands
        assert params["format"] == EapiCommandFormat.TEXT
        assert params["timestamps"] is False
        assert params["autoComplete"] is False
        assert params["expandAliases"] is False
        assert params["stopOnError"] is True

    def test_to_jsonrpc_with_complex_commands(self) -> None:
        """Test JSON-RPC conversion with complex commands."""
        commands: list[EapiSimpleCommand | EapiComplexCommand] = [
            {"cmd": "enable", "input": "password"},
            {"cmd": "configure", "input": ""},
            {"cmd": "hostname test-device"},
        ]
        req = EapiRequest(commands=commands)

        jsonrpc = req.to_jsonrpc()

        # Verify commands are passed correctly
        assert jsonrpc["params"]["cmds"] == commands

    def test_immutability(self) -> None:
        """Test that the dataclass is truly immutable (frozen)."""
        commands: list[EapiSimpleCommand | EapiComplexCommand] = ["show version"]
        req = EapiRequest(commands=commands)

        # Attempting to modify any attribute should raise an error
        with pytest.raises(AttributeError):
            req.commands = ["new command"]  # type: ignore[misc]

        with pytest.raises(AttributeError):
            req.id = "new-id"  # type: ignore[misc]


class TestEapiResponse:
    """Test cases for the EapiResponse class."""

    def test_init_and_properties(self) -> None:
        """Test basic initialization and properties."""
        # Create mock command results
        result1 = EapiCommandResult(command="show version", output={"version": "4.33.2F-40713977.4332F (engineering build)"})
        result2 = EapiCommandResult(command="show hostname", output={"hostname": "DC1-LEAF1A"})

        # Create response with results
        results = {0: result1, 1: result2}
        response = EapiResponse(request_id="test-123", _results=results)

        # Check attributes
        assert response.request_id == "test-123"
        assert response.error_code is None
        assert response.error_message is None

        # Check properties
        assert response.success is True
        assert len(response.results) == 2
        assert response.results[0] == result1
        assert response.results[1] == result2

    def test_error_response(self) -> None:
        """Test initialization with error information."""
        result = EapiCommandResult(command="show bad command", output=None, errors=["Invalid input (at token 1: 'bad')"], success=False)
        results = {0: result}
        response = EapiResponse(
            request_id="test-456", _results=results, error_code=1002, error_message="CLI command 1 of 1 'show bad command' failed: invalid command"
        )

        assert response.request_id == "test-456"
        assert response.error_code == 1002
        assert response.error_message == "CLI command 1 of 1 'show bad command' failed: invalid command"
        assert response.success is False
        assert len(response.results) == 1
        assert response.results[0].success is False
        assert "Invalid input (at token 1: 'bad')" in response.results[0].errors

    def test_len_and_iteration(self) -> None:
        """Test __len__ and __iter__ methods."""
        # Create 3 command results
        results = {
            0: EapiCommandResult(command="cmd1", output="out1"),
            1: EapiCommandResult(command="cmd2", output="out2"),
            2: EapiCommandResult(command="cmd3", output="out3"),
        }
        response = EapiResponse(request_id="test-789", _results=results)

        # Test __len__
        assert len(response) == 3

        # Test __iter__
        iterated_results = list(response)
        assert len(iterated_results) == 3
        assert [r.command for r in iterated_results] == ["cmd1", "cmd2", "cmd3"]

        # Test non-sequential indices
        results = {
            5: EapiCommandResult(command="cmd5", output="out5"),
            2: EapiCommandResult(command="cmd2", output="out2"),
            9: EapiCommandResult(command="cmd9", output="out9"),
        }
        response = EapiResponse(request_id="test-sorted", _results=results)

        # Results should be ordered by index
        iterated_results = list(response)
        assert [r.command for r in iterated_results] == ["cmd2", "cmd5", "cmd9"]
        assert [r.output for r in iterated_results] == ["out2", "out5", "out9"]

    def test_from_jsonrpc_success(self) -> None:
        """Test from_jsonrpc with successful response."""
        # Mock request
        request = EapiRequest(commands=["show version", "show hostname"], format=EapiCommandFormat.JSON)

        # Mock response data
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "test-id-123",
            "result": [{"modelName": "cEOSLab", "version": "4.33.2F-40713977.4332F (engineering build)"}, {"hostname": "DC1-LEAF1A"}],
        }

        response = EapiResponse.from_jsonrpc(jsonrpc_response, request)

        # Verify response object
        assert response.request_id == "test-id-123"
        assert response.success is True
        assert response.error_code is None
        assert response.error_message is None

        # Verify results
        assert len(response) == 2
        assert response.results[0].command == "show version"
        assert response.results[0].output == {"modelName": "cEOSLab", "version": "4.33.2F-40713977.4332F (engineering build)"}
        assert response.results[0].success is True
        assert response.results[1].command == "show hostname"
        assert response.results[1].output == {"hostname": "DC1-LEAF1A"}
        assert response.results[1].success is True

    def test_from_jsonrpc_text_format(self) -> None:
        """Test from_jsonrpc with TEXT format responses."""
        # Mock request with TEXT format
        request = EapiRequest(commands=["show version", "show hostname"], format=EapiCommandFormat.TEXT)

        # Mock response data
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "text-format-id",
            "result": [{"output": "Arista cEOSLab\n\nSoftware image version: 4.33.2F-40713977.4332F"}, {"output": "Hostname: DC1-LEAF1A\nFQDN:     DC1-LEAF1A\n"}],
        }

        response = EapiResponse.from_jsonrpc(jsonrpc_response, request)

        # Verify results contain the text output
        assert len(response) == 2
        assert response.results[0].output is not None
        assert "Arista cEOSLab" in response.results[0].output
        assert response.results[1].output is not None
        assert "Hostname: DC1-LEAF1A" in response.results[1].output

    def test_from_jsonrpc_with_timestamps(self) -> None:
        """Test from_jsonrpc with timestamps enabled."""
        # Mock request with timestamps
        request = EapiRequest(commands=["show version"], format=EapiCommandFormat.JSON, timestamps=True)

        # Mock response data with timestamps
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "timestamp-id",
            "result": [
                {
                    "modelName": "cEOSLab",
                    "version": "4.33.2F-40713977.4332F (engineering build)",
                    "_meta": {"execStartTime": 1741014072.2534037, "execDuration": 0.0024061203002929688},
                }
            ],
        }

        response = EapiResponse.from_jsonrpc(jsonrpc_response, request)

        # Verify timestamp data is processed
        assert len(response) == 1
        assert response.results[0].start_time == 1741014072.2534037
        assert response.results[0].duration == 0.0024061203002929688

        # Verify _meta is removed from output
        assert response.results[0].output is not None
        assert "_meta" not in response.results[0].output

    def test_from_jsonrpc_error_stop_on_error_true(self) -> None:
        """Test from_jsonrpc with error and stop_on_error=True."""
        # Mock request with stop_on_error=True
        request = EapiRequest(commands=["show bad command", "show version", "show hostname"], stop_on_error=True)

        # Mock error response
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "error-id",
            "error": {
                "code": 1002,
                "message": "CLI command 1 of 3 'show bad command' failed: invalid command",
                "data": [{"errors": ["Invalid input (at token 1: 'bad')"]}],
            },
        }

        response = EapiResponse.from_jsonrpc(jsonrpc_response, request)

        # Verify error info
        assert response.request_id == "error-id"
        assert response.error_code == 1002
        assert response.error_message == "CLI command 1 of 3 'show bad command' failed: invalid command"
        assert response.success is False

        # Verify results - should have entries for all commands
        assert len(response) == 3

        # First command failed
        assert response.results[0].command == "show bad command"
        assert response.results[0].output is None
        assert response.results[0].success is False
        assert response.results[0].errors == ["Invalid input (at token 1: 'bad')"]

        # Remaining commands weren't executed due to stop_on_error=True
        assert response.results[1].command == "show version"
        assert response.results[1].output is None
        assert response.results[1].success is False
        assert "Command not executed due to previous error" in response.results[1].errors
        assert response.results[1].was_executed is False

        assert response.results[2].command == "show hostname"
        assert response.results[2].output is None
        assert response.results[2].success is False
        assert "Command not executed due to previous error" in response.results[2].errors
        assert response.results[2].was_executed is False

    def test_from_jsonrpc_error_stop_on_error_false(self) -> None:
        """Test from_jsonrpc with error and stop_on_error=False."""
        # Mock request with stop_on_error=False
        request = EapiRequest(commands=["show bad command", "show version", "show hostname"], stop_on_error=False)

        # Mock response with error for first command but others succeed
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "error-continue-id",
            "error": {
                "code": 1002,
                "message": "CLI command 1 of 3 'show bad command' failed: invalid command",
                "data": [
                    {"errors": ["Invalid input (at token 1: 'bad')"]},
                    {"modelName": "cEOSLab", "version": "4.33.2F-40713977.4332F (engineering build)"},
                    {"hostname": "DC1-LEAF1A"},
                ],
            },
        }

        response = EapiResponse.from_jsonrpc(jsonrpc_response, request)

        # Verify error info
        assert response.request_id == "error-continue-id"
        assert response.error_code == 1002
        assert response.error_message == "CLI command 1 of 3 'show bad command' failed: invalid command"
        assert response.success is False

        # Verify individual command results
        assert len(response) == 3

        # First command failed
        assert response.results[0].command == "show bad command"
        assert response.results[0].output is None
        assert response.results[0].success is False
        assert response.results[0].errors == ["Invalid input (at token 1: 'bad')"]

        # Remaining commands succeeded
        assert response.results[1].command == "show version"
        assert response.results[1].output == {"modelName": "cEOSLab", "version": "4.33.2F-40713977.4332F (engineering build)"}
        assert response.results[1].success is True

        assert response.results[2].command == "show hostname"
        assert response.results[2].output == {"hostname": "DC1-LEAF1A"}
        assert response.results[2].success is True

    def test_from_jsonrpc_raise_on_error(self) -> None:
        """Test from_jsonrpc with raise_on_error=True."""
        # Mock request
        request = EapiRequest(commands=["show bad command"])

        # Mock error response
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "raise-error-id",
            "error": {
                "code": 1002,
                "message": "CLI command 1 of 1 'show bad command' failed: invalid command",
                "data": [{"errors": ["Invalid input (at token 1: 'bad')"]}],
            },
        }

        # Should raise EapiReponseError
        with pytest.raises(EapiReponseError) as excinfo:
            EapiResponse.from_jsonrpc(jsonrpc_response, request, raise_on_error=True)

        # Verify the exception contains the response
        assert excinfo.value.response.request_id == "raise-error-id"
        assert excinfo.value.response.error_code == 1002
        assert excinfo.value.response.error_message == "CLI command 1 of 1 'show bad command' failed: invalid command"

    def test_from_jsonrpc_string_data(self) -> None:
        """Test from_jsonrpc with string data response."""
        # Mock request
        request = EapiRequest(commands=["show bgp ipv4 unicast summary", "show bad command"])

        # Mock response with JSON string
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "EapiExplorer-1",
            "error": {
                "code": 1002,
                "message": "CLI command 2 of 2 'show bad command' failed: invalid command",
                "data": [
                    '{"vrfs":{"default":{"vrf":"default","routerId":"10.1.0.11","asn":"65101","peers":{}}}}\n',
                    {"errors": ["Invalid input (at token 1: 'bad')"]},
                ],
            },
        }

        response = EapiResponse.from_jsonrpc(jsonrpc_response, request)

        # Verify string was parsed as JSON
        assert response.results[0].output == {"vrfs": {"default": {"vrf": "default", "routerId": "10.1.0.11", "asn": "65101", "peers": {}}}}

        # Now test with a non-JSON string
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "EapiExplorer-1",
            "error": {
                "code": 1002,
                "message": "CLI command 2 of 2 'show bad command' failed: invalid command",
                "data": ["This is not JSON", {"errors": ["Invalid input (at token 1: 'bad')"]}],
            },
        }

        response = EapiResponse.from_jsonrpc(jsonrpc_response, request)

        # Verify string is kept as is
        assert response.results[0].output == "This is not JSON"

    def test_from_jsonrpc_complex_commands(self) -> None:
        """Test from_jsonrpc with complex command structures."""
        # Mock request with complex commands
        request = EapiRequest(commands=[{"cmd": "enable", "input": "password"}, "show version"])

        # Mock response
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "complex-cmd-id",
            "result": [{}, {"modelName": "cEOSLab", "version": "4.33.2F-40713977.4332F (engineering build)"}],
        }

        response = EapiResponse.from_jsonrpc(jsonrpc_response, request)

        # Verify command strings are extracted correctly
        assert response.results[0].command == "enable"
        assert response.results[1].command == "show version"
