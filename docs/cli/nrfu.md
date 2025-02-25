---
anta_title: Execute Network Readiness For Use (NRFU) Testing
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

ANTA provides a set of commands for performing NRFU tests on devices. These commands are under the `anta nrfu` namespace and offer multiple output format options:

- [Text report](#performing-nrfu-with-text-rendering)
- [Table report](#performing-nrfu-with-table-rendering)
- [JSON report](#performing-nrfu-with-json-rendering)
- [Custom template report](#performing-nrfu-with-custom-reports)
- [CSV report](#performing-nrfu-and-saving-results-in-a-csv-file)
- [Markdown report](#performing-nrfu-and-saving-results-in-a-markdown-file)

## NRFU Command overview

```bash
--8<-- "anta_nrfu_help.txt"
```

> `username`, `password`, `enable-password`, `enable`, `timeout` and `insecure` values are the same for all devices

All commands under the `anta nrfu` namespace require a catalog yaml file specified with the `--catalog` option and a device inventory file specified with the `--inventory` option.

> [!TIP]
> Issuing the command `anta nrfu` will run `anta nrfu table` without any option.

### Tag management

The `--tags` option can be used to target specific devices in your inventory and run only tests configured with this specific tags from your catalog. Refer to the [dedicated page](tag-management.md) for more information.

### Device and test filtering

Options `--device` and `--test` can be used to target one or multiple devices and/or tests to run in your environment. The options can be repeated. Example: `anta nrfu --device leaf1a --device leaf1b --test VerifyUptime --test VerifyReloadCause`.

### Hide results

Option `--hide` can be used to hide test results in the output or report file based on their status. The option can be repeated. Example: `anta nrfu --hide error --hide skipped`.

## Performing NRFU with text rendering

The `text` subcommand provides a straightforward text report for each test executed on all devices in your inventory.

### Command overview

```bash
--8<-- "anta_nrfu_text_help.txt"
```

### Example

```bash
anta nrfu --device DC1-LEAF1A text
```

![anta nrfu text results](../imgs/anta-nrfu-text-output.png){ loading=lazy width="1600" }

## Performing NRFU with table rendering

The `table` command under the `anta nrfu` namespace offers a clear and organized table view of the test results, suitable for filtering. It also has its own set of options for better control over the output.

### Command overview

```bash
--8<-- "anta_nrfu_table_help.txt"
```

The `--group-by` option show a summarized view of the test results per host or per test.

### Examples

```bash
anta nrfu --tags LEAF table
```

![anta nrfu table results](../imgs/anta-nrfu-table-output.png){ loading=lazy width="1600" }

For larger setups, you can also group the results by host or test to get a summarized view:

```bash
anta nrfu table --group-by device
```

![$1anta nrfu table group_by_host_output](../imgs/anta-nrfu-table-group-by-host-output.png){ loading=lazy width="1600" }

```bash
anta nrfu table --group-by test
```

![$1anta nrfu table group_by_test_output](../imgs/anta-nrfu-table-group-by-test-output.png){ loading=lazy width="1600" }

To get more specific information, it is possible to filter on a single device or a single test:

```bash
anta nrfu --device spine1 table
```

![$1anta nrfu table filter_host_output](../imgs/anta-nrfu-table-filter-host-output.png){ loading=lazy width="1600" }

```bash
anta nrfu --test VerifyZeroTouch table
```

![$1anta nrfu table filter_test_output](../imgs/anta-nrfu-table-filter-test-output.png){ loading=lazy width="1600" }

## Performing NRFU with JSON rendering

The JSON rendering command in NRFU testing will generate an output of all test results in JSON format.

### Command overview

```bash
--8<-- "anta_nrfu_json_help.txt"
```

The `--output` option allows you to save the JSON report as a file. If specified, no output will be displayed in the terminal. This is useful for further processing or integration with other tools.

### Example

```bash
anta nrfu --tags LEAF json
```

![$1anta nrfu json results](../imgs/anta-nrfu-json-output.png){ loading=lazy width="1600" }

## Performing NRFU and saving results in a CSV file

The `csv` command in NRFU testing is useful for generating a CSV file with all tests result. This file can be easily analyzed and filtered by operator for reporting purposes.

### Command overview

```bash
--8<-- "anta_nrfu_csv_help.txt"
```

### Example

![anta nrfu csv results](../imgs/anta_nrfu_csv.png){ loading=lazy width="1600" }

## Performing NRFU and saving results in a Markdown file

The `md-report` command in NRFU testing generates a comprehensive Markdown report containing various sections, including detailed statistics for devices and test categories.

### Command overview

```bash
--8<-- "anta_nrfu_mdreport_help.txt"
```

### Example

![anta nrfu md-report results](../imgs/anta-nrfu-md-report-output.png){ loading=lazy width="1600" }

## Performing NRFU with custom reports

ANTA offers a CLI option for creating custom reports. This leverages the Jinja2 template system, allowing you to tailor reports to your specific needs.

### Command overview

```bash
--8<-- "anta_nrfu_tplreport_help.txt"
```

The `--template` option is used to specify the Jinja2 template file for generating the custom report.

The `--output` option allows you to choose the path where the final report will be saved.

### Example

```bash
anta nrfu --tags LEAF tpl-report --template ./custom_template.j2
```

![$1anta nrfu tpl_results](../imgs/anta-nrfu-tpl-report-output.png){ loading=lazy width="1600" }

The template `./custom_template.j2` is a simple Jinja2 template:

```j2
{% for d in data %}
* {{ d.test }} is [green]{{ d.result | upper}}[/green] for {{ d.name }}
{% endfor %}
```

The Jinja2 template has access to all `TestResult` elements and their values, as described in this [documentation](../api/result.md#anta.result_manager.models.TestResult).

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

## Dry-run mode

It is possible to run `anta nrfu --dry-run` to execute ANTA up to the point where it should communicate with the network to execute the tests. When using `--dry-run`, all inventory devices are assumed to be online. This can be useful to check how many tests would be run using the catalog and inventory.

![$1anta nrfu dry_run](../imgs/anta_nrfu___dry_run.svg){ loading=lazy width="1600" }
