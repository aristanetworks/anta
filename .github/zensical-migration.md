<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Zensical Migration Notes

**Branch:** `feature/migrate-to-zensical`
**Last reviewed:** June 24, 2026

This note documents the decisions, temporary workarounds, and validation steps for migrating ANTA documentation from MkDocs Material to Zensical.

## Current State

ANTA now builds documentation with `zensical 0.0.46`.

The documentation dependency group installs:

- `zensical==0.0.46`
- the Zensical-compatible `mike` fork from `git+https://github.com/squidfunk/mike.git`
- `anta-zensical-extensions`, a local documentation-only package under `.github/zensical_extensions/`

CI and release workflows install the docs dependencies with:

```bash
pip install --group doc -e .github/zensical_extensions
```

After that install step, documentation commands do not need `PYTHONPATH`:

```bash
zensical build --clean
zensical build --strict
mike deploy --push main
mike deploy --update-alias --push "$REF_NAME" stable
```

## Versioned Documentation

Zensical does not have native versioning yet. It currently documents versioning through a Zensical-compatible `mike` fork.

ANTA keeps the existing versioning model:

- `extra.version.provider: mike`
- `main` for the main-branch documentation
- `stable` as the release alias
- existing deployed versions left untouched

Do not switch back to plain PyPI `mike==2.2.0`: it builds with `mkdocs build --clean`, not `zensical build`.

The `mike` plugin config in `mkdocs.yml` is explicit because the Zensical-compatible fork expects these keys during deploy:

```yaml
- mike:
    alias_type: symlink
    redirect_template: null
    deploy_prefix: ""
    canonical_version: null
```

## Temporary Workarounds

### Last Update Footer

Zensical 0.0.46 does not run the MkDocs hook used by `mkdocs-git-revision-date-localized-plugin`, so ANTA cannot keep that plugin for the page "Last update" footer.

ANTA uses `_extensions.zensical_git_dates` from the local `anta-zensical-extensions` package instead. Contributors and CI install it explicitly with `-e .github/zensical_extensions` alongside the root `doc` dependency group. The extension reads the current page path from Zensical's rendering context and sets `page.meta.git_revision_date_localized`, which lets the upstream Zensical/Material `partials/source-file.html` render the normal footer.

This workaround is tied to zensical/backlog#18. Re-test it when upgrading Zensical and remove the local extension once native support exists.

The extension is outside `docs/` because Zensical 0.0.46 copies non-page support files from `docs/` into the generated site.

### Custom Code Hook Shape

This helper is a Python-Markdown extension, not a MkDocs plugin.

Zensical 0.0.46 accepts a `plugins:` key for supported compatibility shims and configuration, but it does not load arbitrary MkDocs plugin classes or call MkDocs lifecycle hooks. The `macros` shim can load custom Python modules, but it registers variables, macros, and filters for page rendering; it is not a global per-page metadata hook for this footer use case.

### GLightbox

ANTA uses Zensical's native `zensical.extensions.glightbox` Markdown extension instead of the external `mkdocs-glightbox` plugin.

The old MkDocs plugin accepted additional options such as `slide_effect`, `background`, `shadow`, `touchNavigation`, `loop`, and `effect`. Zensical's documented native extension does not support those options. ANTA keeps only the supported width setting:

```yaml
- zensical.extensions.glightbox:
    width: 90vw
```

Re-test GLightbox behavior after Zensical upgrades before reintroducing any removed `mkdocs-glightbox` behavior.

### Snippets

`docs/snippets/api_tests_overview.md` was renamed to `docs/snippets/api_tests_overview.txt`.

Reason: Zensical renders Markdown files under `docs/` as pages even when the file is intended only for snippet inclusion. Keeping the snippet in `docs/snippets/` preserves the expected source organization, while the `.txt` suffix prevents it from becoming a rendered documentation page.

## Deliberately Out Of Scope

Historical deployed versions should not be rebuilt just to match the new Zensical UI. After this migration, it is acceptable for `/main/` to use the Zensical UI while older release folders keep the static MkDocs Material output they were originally deployed with.

## Validation

Local validation for this branch:

```bash
uv run --group doc zensical --version
uv run --group doc --with-editable .github/zensical_extensions zensical build --clean
uv run --group doc --with-editable .github/zensical_extensions zensical build --strict
uv run --group doc --with-editable .github/zensical_extensions mike deploy --ignore-remote-status --branch zensical-preview main
```

Expected result:

- `zensical --version` reports `0.0.46`
- clean build reports no issues
- strict build reports no issues
- no-push `mike deploy` builds successfully

Preview checks used during review:

- `/main/` is generated by `zensical-0.0.46`
- the page footer shows "Last update"
- `/main/snippets/api_tests_overview/` returns 404
- `/main/snippets/api_tests_overview.txt` is available as a raw snippet asset

Deploy validation used during review:

- `mike deploy --push --remote origin --branch codex-zensical-deploy-test main`
- `mike deploy --update-alias --push --remote origin --branch codex-zensical-deploy-test v0.0.0-zensical-test stable`

The pushed `versions.json` contained `main`, `v0.0.0-zensical-test`, and the `stable` alias pointing to the fake release version.

The active CI documentation gate is `zensical build --strict`.

## Follow-ups

- Re-test zensical/backlog#18 on each Zensical upgrade and remove `anta-zensical-extensions` when native Git revision metadata is available.
- Re-test GLightbox behavior on each Zensical upgrade if upstream adds support for more of the former `mkdocs-glightbox` option surface.
- Tune search tags after review if Zensical search filters are too broad or too narrow.
- Revisit instant previews from `doc-zensical-enable-instant-preview` after the Zensical migration merges.
- Before changing `main-doc.yml` or `release.yml`, test the full `mike deploy` flow against a throwaway deploy branch instead of the real `gh-pages` branch.
