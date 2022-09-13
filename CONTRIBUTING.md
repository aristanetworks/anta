# Contributions guide

Contributions are welcome.
Please open an issue and submit a PR.

## Requirements

The file [requirements-dev.txt](requirements-dev.txt) has the requiriments.

## To use yamllint

Run the command `yamllint -c .yamllint.yml .`

## To use pylint

Run the command `pylint $(git ls-files '-.py')`

## Git Pre-commit hook

```bash
pip install pre-commit
pre-commit install
```

When running a commit or a pre-commit check:

```
❯ echo "import foobaz" > test.py && git add test.py
❯ pre-commit
pylint...................................................................Failed
- hook id: pylint
- exit code: 22

************* Module test
test.py:1:0: C0114: Missing module docstring (missing-module-docstring)
test.py:1:0: E0401: Unable to import 'foobaz' (import-error)
test.py:1:0: W0611: Unused import foobaz (unused-import)
```

## Continuous Integration

GitHub actions is used to test git pushes and pull requests. The workflows are defined in this [directory](.github/workflows).
We can view the result [here](https://github.com/arista-netdevops-community/network-test-automation/actions)
