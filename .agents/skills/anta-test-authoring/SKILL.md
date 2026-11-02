---
name: anta-test-authoring
description: Create or extend ANTA tests and catalogs from an EOS behavior, with unit, catalog, documentation, and optional read-only vEOS qualification. Do not use for arbitrary network configuration or for running an existing test without authoring or catalog work.
metadata:
  short-description: Author and qualify ANTA tests safely
---

# ANTA test authoring

Use this skill when the user wants to add a new ANTA `AntaTest`, add an
existing test to a catalog, or qualify a new test against EOS/vEOS. The
workflow has two explicit modes:

- `contribute`: add a new built-in `AntaTest` with its unit tests, docstring,
  generated example, and validation evidence.
- `catalog`: compose or validate a user catalog from classes that already
  exist in ANTA.

Do not silently switch between modes. If the request could mean either mode
and the target files differ, ask one focused clarification before writing
anything: do not create a class, test fixture, generated example, catalog,
inventory, or report while the mode is unresolved.

## Safety and scope

- Treat a new class and a user catalog as different deliverables.
- Do not configure, break, repair, or reload a vEOS topology by default.
  Live qualification is read-only. A topology mutation requires explicit
  authorization, a bounded change, and a rollback plan.
- Use `LAB_USERNAME` from the invoking environment for the vEOS username.
  Do not guess a username or a password. If eAPI needs a password, use an
  interactive prompt or an already-approved secret mechanism; never write it
  to an inventory, catalog, fixture, report, or Git file.
- Keep live inventories, raw JSON, reports, and credentials in a temporary
  directory outside the repository. Remove them after validation.
- Never edit OpenSpec artifacts as a side effect. Update a proposal, design,
  spec, or task only when the user explicitly asks for that OpenSpec change.
- In `contribute` mode, restrict code edits to the selected ANTA module, its
  matching unit-test module, generated examples, and explicitly requested
  documentation. Show the resulting diff before handoff.
- In `catalog` mode, modify only the user-selected catalog. If no target path
  is supplied, create a temporary preview instead of choosing a project file.

## 1. Select the mode and build the contract

First inspect the request and classify it:

| Request signal | Mode | Primary output |
| --- | --- | --- |
| “Create/add a new test”, new behavior, or missing class | `contribute` | ANTA class plus tests and generated example |
| “Add `VerifyFoo` to my catalog”, existing class and target YAML | `catalog` | User catalog entry and validation |

Before editing, inspect the relevant module and neighboring tests with `rg`
and read the repository guidance. Identify:

- the requested behavior and category;
- existing classes, commands, custom types, and unit fixtures that are close;
- the EOS command and whether its output is text or JSON;
- the required eAPI revision for JSON output;
- mandatory and optional inputs and their validation types;
- success, failure, skipped, error, and atomic-result semantics;
- target EOS releases and the vEOS devices available for qualification.

Present a concise contract before writing in `contribute` mode:

```text
Class/module:
Command(s) and revision(s):
Inputs:
Success and failure conditions:
Atomic results:
Unit scenarios:
Live qualification matrix:
Files allowed to change:
```

Treat this contract as a write gate. Once the mode and behavior are clear,
state the exact allowlist of files and generated outputs, then wait for the
user's confirmation when the requested changes are material or the request
was initially ambiguous. Never expand the allowlist implicitly. If the user
clarifies the mode, restate the contract and allowlist before writing.

Resolve duplicate names, incompatible existing behavior, missing inputs, or
an unknown command before implementation. Do not create a second class just
because a similar class has a different name.

## 2. Follow ANTA contribution conventions

Read [anta-test-conventions.md](references/anta-test-conventions.md) before
implementing `contribute` mode. The essential rules are:

1. Add the class to the existing `anta/tests/<domain>.py` module when the
   domain already exists; create a new module only when the domain is truly
   new.
2. Define `categories`, `commands`, and an `Input` model when inputs are
   required. Use `AntaCommand` for fixed commands and `AntaTemplate` only when
   input values must render commands.
3. Pin the eAPI `revision` for JSON commands after checking the live schema.
4. Implement `test()` with `@AntaTest.anta_test`, consume
   `instance_commands`, and set a terminal result. Use atomic results only
   when the test contract needs per-item diagnostics.
5. Add the expected-results and YAML catalog example to the class docstring.
6. Add success, failure, missing-data, invalid-input, and version/platform
   cases to the matching `tests/units/anta_tests/test_<domain>.py` `DATA`
   mapping. Include expected messages and atomic results when produced.
7. Regenerate `examples/tests.yaml`; do not hand-edit generated entries.

For `catalog` mode, use the existing class and its documented input model.
Create a minimal target catalog, validate it, and keep user-specific files
out of `examples/tests.yaml`.

## 3. Qualify EOS/vEOS without persisting secrets

Read [live-qualification.md](references/live-qualification.md) when live
access is requested. Use the vEOS names documented by the project's lab
notes; a typical matrix is one recent F release, one M release, and the
release that exposes the behavior under test.

The process is:

1. Confirm `LAB_USERNAME` is present in the invoking environment. If it is
   absent, stop and explain how the caller can expose it; do not source an
   arbitrary `.envrc` automatically.
2. Build an inventory without credentials in a temporary directory.
3. Collect the candidate command as JSON with `anta debug run-cmd`, explicitly
   recording the device, EOS version, command, format, and revision in the
   temporary evidence only.
4. Compare the relevant JSON shape across the F/M/target releases. Choose a
   compatible revision or propose a version-specific implementation. If the
   shape differs materially, do not claim cross-release support.
5. Run the temporary catalog with `anta nrfu` when the requested live state is
   available. Report separately whether the result is live success, live
   failure, fixture-only evidence, or blocked by access/topology.
6. Use fixtures for negative branches unless a known non-established state is
   already present. Do not create a failure by changing a shared vEOS device.

The live qualification is evidence for the contract; it does not replace
unit fixtures or make an unavailable state pass.

## 4. Validate and hand off

For `catalog` mode, run at least:

```bash
uv run anta check catalog --catalog <catalog.yml>
uv run anta get commands --catalog <catalog.yml>
```

For `contribute` mode, regenerate examples and run the narrow checks first:

```bash
uv run python docs/scripts/generate_examples_tests.py
uv run anta check catalog --catalog examples/tests.yaml
uv run pytest tests/units/anta_tests/test_<domain>.py
```

Then run the repository checks appropriate to the change:

```bash
uv run pytest tests/units
tox -e lint
tox -e type
pre-commit run --all-files
zensical build --clean --strict
```

Do not declare the change ready when a required check fails. The final
handoff must separate:

- files changed and generated files;
- catalog and unit-test evidence;
- documentation, lint, and type-check evidence;
- live vEOS evidence by release, command, and result;
- blocked or unqualified cases;
- confirmation that no credential or private live artifact was retained.

If work stopped before writing, report that no target files or generated
artifacts were created and include the clarification still required.

## 5. Independent forward testing

When validating this skill itself, follow
[forward-tests.md](references/forward-tests.md). Always use a temporary copy
or detached worktree, not the working repository as the write target. Verify
the main repository status before and after each scenario, scan temporary
artifacts with `scripts/scan_sensitive_artifacts.py`, and remove the temporary
workspace after collecting the test outcome.
