# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# Initially written by Jeremy Schulman at https://github.com/jeremyschulman/aio-eapi
"""asynceapi.SessionConfig definition."""

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .device import Device

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["SessionConfig"]

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


class SessionConfig:
    """
    Send configuration to a device using the EOS session mechanism.

    This is the preferred way of managing configuration changes.

    Notes
    -----
        This class definition is used by the parent Device class definition as
        defined by `config_session`. A Caller can use the SessionConfig directly
        as well, but it is not required.
    """

    CLI_CFG_FACTORY_RESET = "rollback clean-config"

    def __init__(self, device: Device, name: str) -> None:
        """
        Create a new instance of SessionConfig.

        The session config instance bound
        to the given device instance, and using the session `name`.

        Parameters
        ----------
        device
            The associated device instance.
        name
            The name of the config session.
        """
        self._device = device
        self._cli = device.cli
        self._name = name
        self._cli_config_session = f"configure session {self.name}"

    # -------------------------------------------------------------------------
    # properties for read-only attributes
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return read-only session name attribute."""
        return self._name

    @property
    def device(self) -> Device:
        """Return read-only device instance attribute."""
        return self._device

    # -------------------------------------------------------------------------
    #                               Public Methods
    # -------------------------------------------------------------------------

    async def status_all(self) -> dict[str, Any]:
        """
        Get the status of all the session config on the device.

        Run the following command on the device:
            # show configuration sessions detail

        Returns
        -------
        dict[str, Any]
            Dictionary of native EOS eAPI response; see `status` method for
            details.

        Examples
        --------
        Return example:

        ```
        {
            "maxSavedSessions": 1,
            "maxOpenSessions": 5,
            "sessions": {
                "jeremy1": {
                    "instances": {},
                    "state": "pending",
                    "commitUser": "",
                    "description": ""
                },
                "ansible_167510439362": {
                    "instances": {},
                    "state": "completed",
                    "commitUser": "joe.bob",
                    "description": "",
                    "completedTime": 1675104396.4500246
                }
            }
        }
        ```
        """
        return await self._cli("show configuration sessions detail")  # type: ignore[return-value] # json outformat returns dict[str, Any]

    async def status(self) -> dict[str, Any] | None:
        """
        Get the status of a session config on the device.

        Run the following command on the device:
            # show configuration sessions detail

        And return only the status dictionary for this session. If you want
        all sessions, then use the `status_all` method.

        Returns
        -------
        dict[str, Any] | None
            Dictionary instance of the session status. If the session does not exist,
            then this method will return None.

        Examples
        --------
        The return is the native eAPI results from JSON output:

        ```
        all results:
            {
                "maxSavedSessions": 1,
                "maxOpenSessions": 5,
                "sessions": {
                    "jeremy1": {
                        "instances": {},
                        "state": "pending",
                        "commitUser": "",
                        "description": ""
                    },
                    "ansible_167510439362": {
                        "instances": {},
                        "state": "completed",
                        "commitUser": "joe.bob",
                        "description": "",
                        "completedTime": 1675104396.4500246
                    }
                }
            }
        ```

        If the session name was 'jeremy1', then this method would return:

        ```
        {
            "instances": {},
            "state": "pending",
            "commitUser": "",
            "description": ""
        }
        ```
        """
        res = await self.status_all()
        return res["sessions"].get(self.name)

    async def push(self, content: list[str] | str, *, replace: bool = False) -> None:
        """
        Send the configuration content to the device.

        If `replace` is true, then the command "rollback clean-config" is issued
        before sending the configuration content.

        Parameters
        ----------
        content
            The text configuration CLI commands, as a list of strings, that
            will be sent to the device.  If the parameter is a string, and not
            a list, then split the string across linebreaks.  In either case
            any empty lines will be discarded before they are send to the
            device.
        replace
            When True, the content will replace the existing configuration
            on the device.
        """
        # if given s string, we need to break it up into individual command
        # lines.

        if isinstance(content, str):
            content = content.splitlines()

        # prepare the initial set of command to enter the config session and
        # rollback clean if the `replace` argument is True.

        commands: list[str | dict[str, Any]] = [self._cli_config_session]
        if replace:
            commands.append(self.CLI_CFG_FACTORY_RESET)

        # add the Caller's commands, filtering out any blank lines. any command
        # lines (!) are still included.

        commands.extend(filter(None, content))

        await self._cli(commands=commands)

    async def commit(self, timer: str | None = None) -> None:
        """
        Commit the session config.

        Run the following command on the device:
            # configure session <name>
            # commit

        Parameters
        ----------
        timer
            If the timer is specified, format is "hh:mm:ss", then a commit timer is
            started.  A second commit action must be made to confirm the config
            session before the timer expires; otherwise the config-session is
            automatically aborted.
        """
        command = f"{self._cli_config_session} commit"

        if timer:
            command += f" timer {timer}"

        await self._cli(command)

    async def abort(self) -> None:
        """
        Abort the configuration session.

        Run the following command on the device:
            # configure session <name> abort
        """
        await self._cli(f"{self._cli_config_session} abort")

    async def diff(self) -> str:
        """
        Return the "diff" of the session config relative to the running config.

        Run the following command on the device:
            # show session-config named <name> diffs

        Returns
        -------
        str
            Return a string in diff-patch format.

        References
        ----------
            * https://www.gnu.org/software/diffutils/manual/diffutils.txt
        """
        return await self._cli(f"show session-config named {self.name} diffs", ofmt="text")  # type: ignore[return-value] # text outformat returns str

    async def load_file(self, filename: str, *, replace: bool = False) -> None:
        """
        Load the configuration from <filename> into the session configuration.

        If the replace parameter is True then the file contents will replace the existing session config (load-replace).

        Parameters
        ----------
        filename
            The name of the configuration file.  The caller is required to
            specify the filesystem, for example, the
            filename="flash:thisfile.cfg".

        replace
            When True, the contents of the file will completely replace the
            session config for a load-replace behavior.

        Raises
        ------
        RuntimeError
            If there are any issues with loading the configuration file then a
            RuntimeError is raised with the error messages content.
        """
        commands: list[str | dict[str, Any]] = [self._cli_config_session]
        if replace:
            commands.append(self.CLI_CFG_FACTORY_RESET)

        commands.append(f"copy {filename} session-config")
        res: list[dict[str, Any]] = await self._cli(commands=commands)  # type: ignore[assignment] # JSON outformat of multiple commands returns list[dict[str, Any]]
        checks_re = re.compile(r"error|abort|invalid", flags=re.IGNORECASE)
        messages = res[-1]["messages"]

        if any(map(checks_re.search, messages)):
            raise RuntimeError("".join(messages))

    async def write(self) -> None:
        """Save the running config to the startup config by issuing the command "write" to the device."""
        await self._cli("write")
