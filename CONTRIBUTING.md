# Contributions guide

Contributions are welcome.
Please open an issue and submit a PR.

## Requirements

To contribute, you can install `dev` packages with following command:

```bash
# Install anta in editable mode (optional)
pip install -e .

# Install dev packages
pip install 'anta[dev]'
```

Then, tox is configued with few environment to run CI locally:

```bash
tox list
default environments:
clean  -> run the test driver with /home/tom/.pyenv/versions/3.9.9/envs/arista-anta/bin/python3.9
py38   -> run the test driver with py38
py39   -> run the test driver with py39
py310  -> run the test driver with py310
lint   -> check the code style
type   -> check typing
report -> run the test driver with /home/tom/.pyenv/versions/3.9.9/envs/arista-anta/bin/python3.9

additional environments:
3.8    -> run the test driver with 3.8
3.9    -> run the test driver with 3.9
3.10   -> run the test driver with 3.10
```

## Code linting

```bash
tox -e lint
[...]
lint: commands[0]> flake8 --max-line-length=165 --config=/dev/null anta
lint: commands[1]> flake8 --max-line-length=165 --config=/dev/null scripts
lint: commands[2]> flake8 --max-line-length=165 --config=/dev/null tests
lint: commands[3]> pylint anta

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

lint: commands[4]> pylint scripts

-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 7.15/10, +2.85)

.pkg: _exit> python /home/tom/.pyenv/versions/3.9.9/envs/arista-anta/lib/python3.9/site-packages/pyproject_api/_backend.py True setuptools.build_meta
  lint: OK (28.37=setup[7.03]+cmd[0.38,0.23,0.25,11.07,9.41] seconds)
  congratulations :) (28.45 seconds)
```

## Code Typing

```bash
tox -e type

type: commands[0]> mypy --config-file=pyproject.toml anta
Success: no issues found in 38 source files
type: commands[1]> mypy --config-file=pyproject.toml scripts
Success: no issues found in 6 source files
.pkg: _exit> python /home/tom/.pyenv/versions/3.9.9/envs/arista-anta/lib/python3.9/site-packages/pyproject_api/_backend.py True setuptools.build_meta
  type: OK (28.80=setup[24.54]+cmd[3.35,0.90] seconds)
  congratulations :) (28.89 seconds)
```

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
