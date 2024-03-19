<!--
  ~ Copyright (c) 2023-2024 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Execute Network Readiness For Use (NRFU) Testing

ANTA provides a set of commands for performing NRFU tests on devices. These commands are under the `anta nrfu` namespace and offer multiple output format options:

- [Text view](#performing-nrfu-with-text-rendering)
- [Table view](#performing-nrfu-with-table-rendering)
- [JSON view](#performing-nrfu-with-json-rendering)
- [Custom template view](#performing-nrfu-with-custom-reports)

### NRFU Command overview

```bash
anta nrfu --help
Usage: anta nrfu [OPTIONS] COMMAND [ARGS]...

  Run ANTA tests on devices.

Options:
  -u, --username TEXT     Username to connect to EOS  [env var: ANTA_USERNAME;
                          required]
  -p, --password TEXT     Password to connect to EOS that must be provided. It
                          can be prompted using '--prompt' option.  [env var:
                          ANTA_PASSWORD]
  --enable-password TEXT  Password to access EOS Privileged EXEC mode. It can
                          be prompted using '--prompt' option. Requires '--
                          enable' option.  [env var: ANTA_ENABLE_PASSWORD]
  --enable                Some commands may require EOS Privileged EXEC mode.
                          This option tries to access this mode before sending
                          a command to the device.  [env var: ANTA_ENABLE]
  -P, --prompt            Prompt for passwords if they are not provided.  [env
                          var: ANTA_PROMPT]
  --timeout INTEGER       Global connection timeout  [env var: ANTA_TIMEOUT;
                          default: 30]
  --insecure              Disable SSH Host Key validation  [env var:
                          ANTA_INSECURE]
  --disable-cache         Disable cache globally  [env var:
                          ANTA_DISABLE_CACHE]
  -i, --inventory FILE    Path to the inventory YAML file  [env var:
                          ANTA_INVENTORY; required]
  -t, --tags TEXT         List of tags using comma as separator:
                          tag1,tag2,tag3  [env var: ANTA_TAGS]
  -c, --catalog FILE      Path to the test catalog YAML file  [env var:
                          ANTA_CATALOG; required]
  --ignore-status         Always exit with success  [env var:
                          ANTA_NRFU_IGNORE_STATUS]
  --ignore-error          Only report failures and not errors  [env var:
                          ANTA_NRFU_IGNORE_ERROR]
  -d, --device TEXT       Show a summary for this device
  --test TEXT             Show a summary for this test
  --help                  Show this message and exit.

Commands:
  json        ANTA command to check network state with JSON result.
  table       ANTA command to check network states with table result.
  text        ANTA command to check network states with text result.
  tpl-report  ANTA command to check network state with templated report.
```

> `username`, `password`, `enable-password`, `enable`, `timeout` and `insecure` values are the same for all devices

All commands under the `anta nrfu` namespace require a catalog yaml file specified with the `--catalog` option and a device inventory file specified with the `--inventory` option.

!!! info
    Issuing the command `anta nrfu` will run `anta nrfu table` without any option.

## Tag management

The `--tags` option can be used to target specific devices in your inventory and run only tests configured with this specific tags from your catalog. The default tag is set to `all` and is implicit. Expected behaviour is provided below:

| Command | Description |
| ------- | ----------- |
| `none` | Run all tests on all devices according `tag` definition in your inventory and test catalog. And tests with no tag are executed on all devices|
| `--tags leaf` | Run all tests marked with `leaf` tag on all devices configured with `leaf` tag.<br/> All other tags are ignored |
| `--tags leaf,spine` | Run all tests marked with `leaf` tag on all devices configured with `leaf` tag.<br/>Run all tests marked with `spine` tag on all devices configured with `spine` tag.<br/> All other tags are ignored |

!!! info
    [More examples](tag-management.md) available on this dedicated page.

## Device and test filtering

Options `--device` and `--test` can be used to target a specific device and/or test to run in your environment. These 2 options are not compatible with the `--tags` option.

## Performing NRFU with text rendering

The `text` subcommand provides a straightforward text report for each test executed on all devices in your inventory.

### Command overview

```bash
anta nrfu text --help
Usage: anta nrfu text [OPTIONS]

  ANTA command to check network states with text result.

Options:
  --skip-error    Hide tests in errors due to connectivity issue
  --skip-failure  Hide tests in failure
  --skip-success  Hide tests in success to focus on error or failure
  --help          Show this message and exit.
```

The `--skip-error` option can be used to exclude tests that failed due to connectivity issues or unsupported commands. Same behavior applied to `--skip-failure` to skip tests in failure and `--skip-success` to skip tests in success.

### Example

```bash
anta nrfu --device DC1-LEAF1A text
```
[![anta nrfu text results](../imgs/anta-nrfu-text-output.png){ loading=lazy width="1600" }](../imgs/anta-nrfu-text-output.png)

## Performing NRFU with table rendering

The `table` command under the `anta nrfu` namespace offers a clear and organized table view of the test results, suitable for filtering. It also has its own set of options for better control over the output.

### Command overview

```bash
anta nrfu table --help
Usage: anta nrfu table [OPTIONS]

  ANTA command to check network states with table result.

Options:
  --group-by [device|test]  Group result by test or host. default none
  --skip-error              Hide tests in errors due to connectivity issue
  --skip-failure            Hide tests in failure
  --skip-success            Hide tests in success to focus on error or failure
  --help                    Show this message and exit.
```

The `--group-by` option show a summarized view of the test results per host or per test.

The `--skip-error` option can be used to exclude tests that failed due to connectivity issues or unsupported commands. Same behavior applied to `--skip-failure` to skip tests in failure and `--skip-success` to skip tests in success.

### Examples

```bash
anta nrfu --tags LEAF table
```
[![anta nrfu table results](../imgs/anta-nrfu-table-output.png){ loading=lazy width="1600" }](../imgs/anta-nrfu-table-output.png)

For larger setups, you can also group the results by host or test to get a summarized view:

```bash
anta nrfu table --group-by device
```
[![anta nrfu table group_by_host_output](../imgs/anta-nrfu-table-group-by-host-output.png){ loading=lazy width="1600" }](../imgs/anta-nrfu-table-group-by-host-output.png)

```bash
anta nrfu table --group-by test
```
[![anta nrfu table group_by_test_output](../imgs/anta-nrfu-table-group-by-test-output.png){ loading=lazy width="1600" }](../imgs/anta-nrfu-table-group-by-test-output.png)

To get more specific information, it is possible to filter on a single device or a single test:

```bash
anta nrfu --device spine1 table
```
[![anta nrfu table filter_host_output](../imgs/anta-nrfu-table-filter-host-output.png){ loading=lazy width="1600" }](../imgs/anta-nrfu-table-filter-host-output.png)

```bash
anta nrfu --test VerifyZeroTouch table
```
[![anta nrfu table filter_test_output](../imgs/anta-nrfu-table-filter-test-output.png){ loading=lazy width="1600" }](../imgs/anta-nrfu-table-filter-test-output.png)

## Performing NRFU with JSON rendering

The JSON rendering command in NRFU testing is useful in generating a JSON output that can subsequently be passed on to another tool for reporting purposes.

### Command overview

```bash
anta nrfu json --help
Usage: anta nrfu json [OPTIONS]

  ANTA command to check network state with JSON result.

Options:
  -o, --output FILE  Path to save report as a file  [env var:
                     ANTA_NRFU_JSON_OUTPUT]
  --help             Show this message and exit.
```

The `--output` option allows you to save the JSON report as a file.

### Example

```bash
anta nrfu --tags LEAF json
```
[![anta nrfu json results](../imgs/anta-nrfu-json-output.png){ loading=lazy width="1600" }](../imgs/anta-nrfu-json-output.png)

## Performing NRFU with custom reports

ANTA offers a CLI option for creating custom reports. This leverages the Jinja2 template system, allowing you to tailor reports to your specific needs.

### Command overview

```bash
anta nrfu tpl-report --help
Usage: anta nrfu tpl-report [OPTIONS]

  ANTA command to check network state with templated report

Options:
  -tpl, --template FILE  Path to the template to use for the report  [env var:
                         ANTA_NRFU_TPL_REPORT_TEMPLATE; required]
  -o, --output FILE      Path to save report as a file  [env var:
                         ANTA_NRFU_TPL_REPORT_OUTPUT]
  --help                 Show this message and exit.
```
The `--template` option is used to specify the Jinja2 template file for generating the custom report.

The `--output` option allows you to choose the path where the final report will be saved.

### Example

```bash
anta nrfu --tags LEAF tpl-report --template ./custom_template.j2
```
[![anta nrfu json results](../imgs/anta-nrfu-tpl-report-output.png){ loading=lazy width="1600" }](../imgs/anta-nrfu-tpl-report-output.png)

The template `./custom_template.j2` is a simple Jinja2 template:

```j2
{% for d in data %}
* {{ d.test }} is [green]{{ d.result | upper}}[/green] for {{ d.name }}
{% endfor %}
```

The Jinja2 template has access to all `TestResult` elements and their values, as described in this [documentation](../api/result_manager_models.md#testresult-entry).

You can also save the report result to a file using the `--output` option:

```bash
anta nrfu --tags LEAF tpl-report --template ./custom_template.j2 --output nrfu-tpl-report.txt
```

The resulting output might look like this:

```bash
cat nrfu-tpl-report.txt
* VerifyMlagStatus is [green]SUCCESS[/green] for DC1-LEAF1A
* VerifyMlagInterfaces is [green]SUCCESS[/green] for DC1-LEAF1A
* VerifyMlagConfigSanity is [green]SUCCESS[/green] for DC1-LEAF1A
* VerifyMlagReloadDelay is [green]SUCCESS[/green] for DC1-LEAF1A
```
