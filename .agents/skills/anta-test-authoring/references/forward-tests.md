# Independent forward tests

These scenarios validate the skill itself, not ANTA runtime behavior. Run them
in a temporary copy or detached worktree outside the working repository.

## Scenario A: existing class in a catalog

Use a request such as:

> Add the existing `anta.tests.services.VerifyHostname` test to a temporary
> catalog for the device tag `veos`, validate its inputs, and show the command
> that will run. Do not modify ANTA source files.

Expected evidence:

- only the temporary catalog changes;
- `uv run anta check catalog --catalog <temporary-catalog>` succeeds;
- `uv run anta get commands --catalog <temporary-catalog>` resolves the test;
- the source module, unit tests, and `examples/tests.yaml` are unchanged.

## Scenario B: new built-in test

Use a request such as:

> In an isolated copy, create a new built-in system test for a stated JSON EOS
> command and expected state. Add the `AntaTest` class, typed inputs if needed,
> unit fixtures for success and failure, and the generated catalog example.
> Qualify the command read-only on the documented F/M vEOS targets if access
> is available. Do not modify the original ANTA workspace.

Expected evidence:

- the contract is shown before implementation;
- the class, matching `DATA` cases, docstring example, and generated catalog
  entry are present only in the temporary copy;
- targeted pytest, catalog parsing, and example generation succeed;
- live results are reported per release or explicitly marked blocked;
- the original repository has no new files or modified tracked files.

## Isolation checks

Before and after each scenario:

```bash
git -C <original-repository> status --short
git -C <temporary-workspace> diff --check
```

Scan any retained temporary evidence before reviewing it:

```bash
python <skill-root>/scripts/scan_sensitive_artifacts.py /tmp/anta-live
```

Remove the temporary workspace and raw live evidence after the outcome is
recorded. Do not copy the generated patch back to the original repository.
