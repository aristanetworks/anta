<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Regenerating documentation output snapshots

This maintainer runbook describes how to refresh ANTA CLI output embedded in the documentation. It is intentionally kept outside the public documentation because the private lab paths and capture workflow are not user-facing ANTA guidance.

## Choose the capture type

- Keep `--help` output as searchable text. Run `uv run --extra cli python docs/scripts/generate_doc_snippets.py` to update the text files under `docs/snippets/` and the literal help block in `README.md`. The README cannot use a snippet include because the same file is rendered on PyPI.
- Use `docs/scripts/generate_snippet.py --format svg` for terminal output shown in documentation pages.
- Use `--format txt` only when a new searchable text snippet is required.

The capture options must come before `anta`:

```bash
uv run --extra cli python docs/scripts/generate_snippet.py \
  --format svg \
  --max-results 5 \
  anta ...
```

`--max-results` limits NRFU results before a report is rendered. Use it for long table, text, or JSON examples, but omit it when every result is intentionally visible, such as a small grouped report or a CSV/Markdown example. `--max-lines` limits recorded terminal lines while preserving the final status line; use it for verbose commands whose output is not backed by a `ResultManager`.

The script prints the generated path. Its filename is derived from the complete ANTA command, so update the Markdown image reference if the command changes. Do not hand-edit generated SVG content.

## Load the documentation lab

Private lab files live in the main checkout's ignored `.personal/` directory so they are available to stacked worktrees without being committed. Resolve that directory from Git's common directory, load the environment, and verify the expected inputs before connecting:

TODO: Make these fixtures available to maintainers so snapshots can be regenerated from any environment and potentially automated in CI.

```bash
ANTA_PRIVATE_DIR="$(cd "$(git rev-parse --git-common-dir)/.." && pwd)/.personal"

test -f "$ANTA_PRIVATE_DIR/doc_env"
test -f "$ANTA_PRIVATE_DIR/doc_inventory.yml"
test -f "$ANTA_PRIVATE_DIR/doc_catalog.yml"

set -a
source "$ANTA_PRIVATE_DIR/doc_env"
set +a
```

Run captures from the worktree root. For example:

```bash
uv run --extra cli python docs/scripts/generate_snippet.py \
  --format svg \
  --max-results 5 \
  anta \
  --inventory "$ANTA_PRIVATE_DIR/doc_inventory.yml" \
  --catalog "$ANTA_PRIVATE_DIR/doc_catalog.yml" \
  nrfu --tags leaf table
```

Use the command displayed in the target documentation page as the source of truth. Match its device, tag, catalog, and report options exactly. Do not regenerate PSIRT snapshots unless the PSIRT lab is available and its expected advisory state has been confirmed.

## Documentation-only custom tests

The custom-test example is reproducible with the committed package under `docs/fixtures/`; it does not require installing a public Python package. Add that directory to `PYTHONPATH` only for the capture command:

```bash
PYTHONPATH=docs/fixtures uv run --extra cli python docs/scripts/generate_snippet.py \
  --format svg \
  --max-results 5 \
  anta \
  --inventory "$ANTA_PRIVATE_DIR/doc_inventory.yml" \
  --catalog docs/snippets/custom-tests-catalog.yml \
  nrfu --device dc1-spine1 text
```

Keep this implementation detail in maintainer instructions or Markdown source comments; the public custom-test page should explain how custom tests work, not how ANTA's documentation fixture is wired.

## Review and validate

Before committing a regenerated snapshot:

1. Compare it with the command and surrounding explanation on the page.
2. Confirm the capture contains the command header and final outcome, uses reasonable result or line limits, and does not expose passwords, tokens, private addresses, or unrelated environment details.
3. Reference local SVGs with `class="img_center"`, `loading=lazy`, and the established page width.
4. Remove report files produced only as command side effects, but keep the generated SVG under `docs/imgs/`.
5. Check `git status` and the diff to ensure `.personal/`, generated reports, and `site/` are not staged.

Run the focused tests and documentation checks:

```bash
uv run --extra cli --group test pytest tests/docs/test_generate_snippet.py tests/docs/test_doc_output_examples.py
pre-commit run --files <changed-file> [<changed-file> ...]
uv run --group doc --with-editable tools/zensical_extensions zensical build --clean --strict
```
