---
toc_depth: 3
anta_title: Frequently Asked Questions (FAQ)
---
<!--
  ~ Copyright (c) 2023-2024 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->
<style>
  .md-typeset h3 {
    visibility: hidden;
    font-size: 0em;
    height: 0em;
    line-height: 0;
    padding: 0;
    margin: 0;
  }
  .md-typeset details {
    margin-top: 0em;
    margin-bottom: 0.8em;
  }
</style>

## A local OS error occurred while connecting to a device

???+ faq "A local OS error occurred while connecting to a device"

    When running ANTA, you can receive `A local OS error occurred while connecting to <device>` errors. The underlying [`OSError`](https://docs.python.org/3/library/exceptions.html#OSError) exception can have various reasons: `[Errno 24] Too many open files` or `[Errno 16] Device or resource busy`.

    This usually means that the operating system refused to open a new file descriptor (or socket) for the ANTA process. This might be due to the hard limit for open file descriptors currently set for the ANTA process.

    At startup, ANTA sets the soft limit of its process to the hard limit up to 16384. This is because the soft limit is usually 1024 and the hard limit is usually higher (depends on the system). If the hard limit of the ANTA process is still lower than the number of selected tests in ANTA, the ANTA process may request to the operating system too many file descriptors and get an error, a WARNING is displayed at startup if this is the case.

    ### Solution

    One solution could be to raise the hard limit for the user starting the ANTA process.
    You can get the current hard limit for a user using the command `ulimit -n -H` while logged in.
    Create the file `/etc/security/limits.d/10-anta.conf` with the following content:
    ```
    <user> hard nofile <value>
    ```
    The `user` is the one with which the ANTA process is started.
    The `value` is the new hard limit. The maximum value depends on the system. A hard limit of 16384 should be sufficient for ANTA to run in most high scale scenarios. After creating this file, log out the current session and log in again.

## `Timeout` error in the logs

???+ faq "`Timeout` error in the logs"

    When running ANTA, you can receive `<Foo>Timeout` errors in the logs (could be ReadTimeout, WriteTimeout, ConnectTimeout or PoolTimeout). More details on the timeouts of the underlying library are available here: https://www.python-httpx.org/advanced/timeouts.

    This might be due to the time the host on which ANTA is run takes to reach the target devices (for instance if going through firewalls, NATs, ...) or when a lot of tests are being run at the same time on a device (eAPI has a queue mechanism to avoid exhausting EOS resources because of a high number of simultaneous eAPI requests).

    ### Solution

    Use the `timeout` option. As an example for the `nrfu` command:

    ```bash
    anta nrfu --enable --username username --password arista --inventory inventory.yml -c nrfu.yml --timeout 50 text
    ```

    The previous command set a couple of options for ANTA NRFU, one them being the `timeout` command, by default, when running ANTA from CLI, it is set to 30s.
    The timeout is increased to 50s to allow ANTA to wait for API calls a little longer.

## `ImportError` related to `urllib3`

???+ faq "`ImportError` related to `urllib3` when running ANTA"

    When running the `anta --help` command, some users might encounter the following error:

    ```bash
    ImportError: urllib3 v2.0 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'OpenSSL 1.0.2k-fips  26 Jan 2017'. See: https://github.com/urllib3/urllib3/issues/2168
    ```

    This error arises due to a compatibility issue between `urllib3` v2.0 and older versions of OpenSSL.

    ### Solution

    1. _Workaround_: Downgrade `urllib3`

        If you need a quick fix, you can temporarily downgrade the `urllib3` package:

        ```bash
        pip3 uninstall urllib3

        pip3 install urllib3==1.26.15
        ```

    2. _Recommended_: Upgrade System or Libraries:

            As per the [urllib3 v2 migration guide](https://urllib3.readthedocs.io/en/latest/v2-migration-guide.html), the root cause of this error is an incompatibility with older OpenSSL versions. For example, users on RHEL7 might consider upgrading to RHEL8, which supports the required OpenSSL version.

## `AttributeError: module 'lib' has no attribute 'OpenSSL_add_all_algorithms'`

???+ faq "`AttributeError: module 'lib' has no attribute 'OpenSSL_add_all_algorithms'` when running ANTA"

    When running the `anta` commands after installation, some users might encounter the following error:

    ```bash
    AttributeError: module 'lib' has no attribute 'OpenSSL_add_all_algorithms'
    ```

    The error is a result of incompatibility between `cryptography` and `pyopenssl` when installing `asyncssh` which is a requirement of ANTA.

    ### Solution

    1. Upgrade `pyopenssl`

        ```bash
        pip install -U pyopenssl>22.0
        ```

## Caveat running on non-POSIX platforms (e.g. Windows)

???+ faq "Caveat running on non-POSIX platforms (e.g. Windows)"

    While ANTA should in general work on non-POSIX platforms (e.g. Windows),
    there are some known limitations:

    - On non-Posix platforms, ANTA is not able to check and/or adjust the system limit of file descriptors.

    ANTA test suite is being run in the CI on a Windows runner.

## `__NSCFConstantString initialize` error on OSX

???+ faq "`__NSCFConstantString initialize` error on OSX"

    This error occurs because of added security to restrict multithreading in macOS High Sierra and later versions of macOS. https://www.wefearchange.org/2018/11/forkmacos.rst.html

    ### Solution

    1. Set the following environment variable

        ```bash
        export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
        ```

## EOS AAA configuration for an ANTA-only user

???+ faq "EOS AAA configuration for an ANTA-only user"

    Here is a starting guide to configure an ANTA-only user to run ANTA tests on a device.

    !!! warning

        This example is not using TACACS / RADIUS but only local AAA

    1. Configure the following role.

        ```bash
        role anta-users
           10 permit command show
           20 deny command .*
        ```

        You can then add other commands if they are required for your test catalog (`ping` for example) and then tighten down the show commands to only those required for your tests.

    2. Configure the following authorization (You may need to adapt depending on your AAA setup).

        ```bash
        aaa authorization commands all default local
        ```

    3. Configure a user for the role.

        ```bash
        user anta role anta-users secret <secret>
        ```

    4. You can then use the credentials `anta` / `<secret>` to run ANTA against the device and adjust the role as required.

# Still facing issues?

If you've tried the above solutions and continue to experience problems, please follow the [troubleshooting](troubleshooting.md) instructions and report the issue in our [GitHub repository](https://github.com/aristanetworks/anta).
