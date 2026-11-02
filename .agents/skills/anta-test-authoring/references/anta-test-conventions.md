# ANTA test conventions

Use this reference for `contribute` mode. It records the repository-specific
points that are easy to miss; the ANTA documentation remains the authority for
the full API.

## Source and generated files

- Built-in tests live in `anta/tests/<domain>.py`.
- Their unit cases live in `tests/units/anta_tests/test_<domain>.py`.
- The generic pytest harness reads the module-level `DATA` mapping and invokes
  the shared `tests.units.anta_tests.test` function.
- `examples/tests.yaml` is generated from catalog examples in test docstrings
  by `docs/scripts/generate_examples_tests.py`.
- API pages are rendered from Python docstrings; do not manually duplicate a
  class reference in generated API output.

## Class contract

An `AntaTest` normally contains:

```python
class VerifyExample(AntaTest):
    """Expected Results and a YAML catalog example."""

    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show example", revision=1),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        output = self.instance_commands[0].json_output
        if output.get("healthy") is True:
            self.result.is_success()
        else:
            self.result.is_failure("Example is not healthy")
```

When user inputs are required, define `class Input(AntaTest.Input)` with
typed fields and field docstrings. Pydantic validation is part of catalog
loading, so invalid inputs must be tested as catalog-load failures rather than
treated as device runtime errors.

For JSON output, select and pin a command revision after schema qualification.
Use `AntaTemplate` only when an input must change the command itself. A test
that checks multiple independent items may opt into atomic results and should
give each atomic result a stable description.

## Unit fixture contract

Each `DATA` entry contains:

- `eos_data`: one output per declared command;
- `inputs`: values used to instantiate the test input model;
- optional `version` and `platform` metadata;
- `expected.result` and, when relevant, expected message substrings and
  `atomic_results`.

At minimum cover a success and the meaningful failure branches: empty or
missing data, malformed data, non-established state, missing requested item,
and input validation. Keep EOS fixtures minimal but representative of the
live JSON shape.

## Checks

Use the repository's own commands rather than inventing a second validator:

```bash
uv run pytest tests/units/anta_tests/test_<domain>.py
uv run anta check catalog --catalog examples/tests.yaml
uv run python docs/scripts/generate_examples_tests.py
```

After the focused checks, run the full repository gates requested by the
change: unit tests, lint, type checks, pre-commit, and strict documentation.
