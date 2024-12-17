<!--
  ~ Copyright (c) 2023-2024 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Using the VSCode Debugger for ANTA Project

To facilitate the development process, the ANTA project includes a VSCode debugger configuration available under the `.vscode` folder. This allows you to run the CLI using the Python debugger, set breakpoints, and watch variables alongside the code.

## Prerequisites

- Ensure you have Python 3 installed on your system.
- Install the necessary Python dependencies for the ANTA project.
- Install the VSCode Python extension.

## Debugger Configuration

The `.vscode` folder contains the `launch.json` file, which defines the debugger configurations. Here is an example configuration:

```json
// filepath: .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "anta cli nrfu text",
            "type": "debugpy",
            "console": "integratedTerminal",
            "request": "launch",
            "module": "anta.cli",
            "args": [ "nrfu", "text"],
            "envFile": "${workspaceFolder}/.vscode/debugger.env",
            "justMyCode": false
        }
    ]
}
```

## Steps to Use the Debugger

1. Open the Project in VSCode: Open the ANTA project folder in VSCode.

2. **Set Breakpoints**: Navigate to the Python file where you want to set breakpoints. Click on the left margin next to the line numbers to set a breakpoint.

3. **Configure the Debugger**: Open the launch.json file and ensure the configuration is set up as shown above. Modify the args field to include the CLI command and options you want to debug.

4. Start Debugging with the side panel tool or by pressing `F5`:

    4.1 Open the Debug panel by clicking on the Debug icon in the Activity Bar on the side of the window.

    4.2 Select the configuration named "Python: CLI" from the dropdown menu.

    4.3 Click the green play button to start debugging.

5. **Inspect** Variables and Step Through Code:

    5.1 Use the Debug toolbar to step through the code, inspect variables, and evaluate expressions.

    5.2 The Debug Console allows you to interact with the running program.

## Available debugger in anta project

To make life easier, anta project has 2 pre-configured debugger configuration to run anta CLI in debug mode:

- **anta cli nrfu text**: Run anta using CLI to get nrfu in text mode
- **anta cli nrfu table**: Run anta using CLI to get nrfu in text mode

Both are based on a variable file you have to configure prior to run debugger. This file must be named **`.vscode/debugger.env`** and have all the variable you need for running the CLI. Below is an example:

```bash
# .vscode/debugger.env

# Root folder for tests
ANTA_ROOT_FOLDER=.vscode/

# Enable ANTA DEBUG mode
ANTA_DEBUG=true

# Default ANTA credentials
ANTA_USERNAME=ansible
ANTA_PASSWORD=ansible
ANTA_ENABLE=false

# NRFU configuration
ANTA_CATALOG=${ANTA_ROOT_FOLDER}/nrfu.yml
ANTA_INVENTORY=${ANTA_ROOT_FOLDER}/inventory.yml

# Snapshot configuration
ANTA_SNAPSHOT=$(date +%Y-%m-%d-%Hh-%Mmin)-snapshots
ANTA_EXEC_SNAPSHOT_OUTPUT_DIRECTORY=${ANTA_ROOT_FOLDER}/${ANTA_SNAPSHOT}%
```

Because ANTA is not limited to only 2 cli options, you can easily add your own debugger settings if you need to debug a specific part of the code. The full documentation is available on [VSCode website](https://code.visualstudio.com/docs/python/debugging).
