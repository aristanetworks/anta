<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Zensical Documentation Plan

**Baseline:** `upstream/main` at `b57e61ff`, Zensical `0.0.66`
**Implementation branch:** `docs/zensical-improvements`
**Last reviewed:** October 5, 2026

The MkDocs Material migration is merged. This plan records the documentation setup that exists on `upstream/main`, reviews Zensical releases from `0.0.60` through the latest release, and prioritizes improvements. This branch improves guide-to-API links and documents link-preservation rules. Other proposals remain a backlog.

## Current State

ANTA pins `zensical==0.0.66` in `pyproject.toml` and in the Pylint and Pyright pre-commit environments. It uses native `zensical.toml`; there is no active `mkdocs.yml`.

The latest published release at review time is [`0.0.68`](https://github.com/zensical/zensical/releases/tag/v0.0.68), released October 5, 2026. Features from `0.0.67` and `0.0.68` require a future dependency update; they are not capabilities of ANTA's current pin. This audit uses the upstream baseline even if a local checkout still has older pins.

The documentation dependency group includes:

- `zensical==0.0.66`
- the Zensical-compatible `mike` fork pinned to commit `2d4ad799442f4592db8ad53b179bfb33db8c69ac`
- `mkdocs` and `mkdocs-autorefs`, which remain runtime requirements of `mkdocstrings`
- `mkdocstrings[python]~=1.0.6` and `mkdocstrings-python~=2.0.9`, plus Griffe and the deprecation extension

The local `anta-zensical-extensions` package under `tools/zensical_extensions/` is installed separately with `-e`; it is not a member of the root `doc` dependency group.

`mkdocs-material` and `mkdocs-material-extensions` are no longer installed directly. Zensical provides the site theme and emoji helpers, while the remaining MkDocs packages are retained only because `mkdocstrings` imports them.

CI and release workflows install the docs dependencies with:

```bash
pip install --group doc -e tools/zensical_extensions
```

After that install step, documentation commands do not need `PYTHONPATH`:

```bash
zensical build --clean
zensical build --strict
docs/scripts/deploy_doc_version.sh main
docs/scripts/deploy_doc_version.sh "$REF_NAME" --final
```

The deployment commands publish to `origin/gh-pages`. They describe CI behavior, not local validation commands. Prereleases use the deployment script without `--final`.

The upstream baseline enables native search, page search tags in front matter, instant navigation, linked content tabs, code copying, `mkdocstrings`, GLightbox, and custom Mermaid zoom. This branch converts Device/Inventory references in the Python-library guide to object references. API backlinks were evaluated and remain disabled: repeated guide links cluttered the API pages without providing enough useful context. `navigation.instant.preview`, API auto-navigation, redirects, blogs, RSS, social cards, and Markdown exports are not configured. Contributor guidance now describes when to add redirects; no placeholder redirect map is enabled.

## Releases Since 0.0.60

| Release | Relevant changes | Effect on ANTA |
| --- | --- | --- |
| [0.0.60](https://github.com/zensical/zensical/releases/tag/v0.0.60) — Sep 8 | Native `table-reader`; navigation pruning and alternate-link fixes; Windows macro template fix. | Already included. Keep curated TOML navigation and existing Markdown tables unless a generated table source becomes available. |
| [0.0.61](https://github.com/zensical/zensical/releases/tag/v0.0.61) — Sep 11 | Page and anchor redirects, redirect chains and cycle rejection; search/autorefs validation fixes; UI 0.0.29. | Already included. Can preserve links when reorganizing guides or renaming headings. |
| [0.0.62](https://github.com/zensical/zensical/releases/tag/v0.0.62) — Sep 13 | Obsidian callouts; plugin configuration compatibility; watched-config fix; UI 0.0.30 reveals anchors inside collapsed details, tabs, and annotations. | Already included. Deep links into API source/details and tabbed examples deserve regression checks. A new callout convention is unnecessary. |
| [0.0.63](https://github.com/zensical/zensical/releases/tag/v0.0.63) — Sep 19 | Snippet dependents rebuild when sources change; hidden files/directories are excluded; preview root redirects and 404 handling; UI 0.0.31 fixes index-only submenus. | Already included. Particularly useful for `docs/README.md` including root `README.md`, CLI snippets, examples, and the class diagram. Validate preview updates without restarting the server. |
| [0.0.64](https://github.com/zensical/zensical/releases/tag/v0.0.64) — Sep 22 | Native Material-compatible blog; UI 0.0.32 blog templates. | Available but disabled. Consider only with an owner for tutorials/release articles. |
| [0.0.65](https://github.com/zensical/zensical/releases/tag/v0.0.65) — Sep 24 | API backlinks; RSS 2.0/JSON Feed 1.1; `mkdocstrings.enable_inventory`, autorefs settings, and Mike `version_selector` support. | Available. Backlinks were evaluated and declined because of API-page clutter; RSS remains disabled. Keep version selection and object inventories working. |
| [0.0.66](https://github.com/zensical/zensical/releases/tag/v0.0.66) — Sep 28 | `mkdocs-autoapi`/`mkdocs-api-autonav` replacements; all published pages in sitemap; raw HTML `srcset` URL fixes; TOML InlineHilite formatters; UI 0.0.33. | Current pin. UI styles API backlinks, restores GLightbox styles after instant navigation, respects Mermaid label colors, and fixes `/` search. No feature flag is needed for those fixes. |
| [0.0.67](https://github.com/zensical/zensical/releases/tag/v0.0.67) — Sep 30 | Native `social`, `llmstxt`, `exclude`, and `github-admonitions`; custom blog view template fix; UI 0.0.34 adds Copy as Markdown. | Upgrade required. Markdown export/copy and branded link previews are useful candidates; exclusions could reduce published source assets. |
| [0.0.68](https://github.com/zensical/zensical/releases/tag/v0.0.68) — Oct 5 | Native audio/video replacements; closer macros compatibility; UI 0.0.35 uses instant navigation for search results and fixes skip links/ARIA naming. **Requires Python >=3.11.** | Upgrade required. Search and accessibility fixes are useful even without new media. The Python requirement needs explicit documentation-tooling handling while ANTA still supports Python 3.10. |

The UI details above are confirmed by the [UI release notes](https://github.com/zensical/ui/releases). None of these releases implements native Git revision dates or replaces the Mike deployment workflow.

## Native Configuration

`zensical.toml` is the sole documentation configuration. Keeping one configuration avoids drift between native Zensical settings and the legacy MkDocs YAML compatibility layer.

The theme is named `zensical`, which selects the same built-in theme that the former `material` compatibility alias selected without requiring the Material package. Markdown callables that YAML represented with `!!python/name` tags are import strings in TOML, as supported by Zensical. The deeply nested navigation remains an ordered array of single-key tables so labels, paths, and menu order stay unchanged.

Markdown extension names containing dots are quoted literal TOML keys. This preserves the extension order from `mkdocs.yml`; leaving them unquoted would make TOML interpret each dot as a nested table, which Zensical can flatten but only after reordering extension groups. Extension order can affect Python-Markdown processing, so the literal representation is the safer behavior-preserving choice.

Search uses Zensical's enabled-by-default native implementation. Its language is derived from `project.theme.language`, as recommended by Zensical, so the configuration does not carry the unsupported MkDocs `plugins.search.lang` option.

Legacy theme settings that Zensical does not implement (`highlightjs`, `hljs_languages`, `include_search_page`, and `search_index_only`) were removed instead of carrying ignored configuration forward. Code highlighting remains configured through Python-Markdown and Pygments.

## Versioned Documentation

ANTA still uses the Zensical-compatible `mike` fork; releases through `0.0.68` do not replace it with a native deployment/versioning system.

ANTA keeps the existing versioning model:

- `project.extra.version.provider = "mike"`
- `main` for the main-branch documentation
- `stable` as the release alias
- existing final-release builds left untouched

`main-doc.yml` and `release.yml` call `docs/scripts/deploy_doc_version.sh`. It runs Mike, exposes the local `gh-pages` tree through a temporary worktree, calls `manage_doc_versions.py`, and pushes only after normalization. The version selector order is `main`, final releases newest first, then prereleases newest first. A final release updates `stable` and removes prerelease content for that same base version; it does not rebuild older final releases. Both deployment jobs share the `documentation-gh-pages` concurrency group.

Do not switch back to plain PyPI `mike==2.2.0`: it builds with `mkdocs build --clean`, not `zensical build`.

The `mike` fork is pinned to an immutable commit SHA in `pyproject.toml` so documentation builds do not drift when the fork's default branch changes.

The supported Mike settings remain explicit in `zensical.toml`:

```toml
[project.plugins.mike]
alias_type = "symlink"
deploy_prefix = ""
canonical_version = "stable"
```

`canonical_version` sets each page's canonical URL to its equivalent in the `stable` alias, helping search engines consolidate versioned copies. It does not guarantee that a page introduced only on `main` exists in `stable`; check that case when adding pages. `redirect_template` is omitted because TOML has no null value; the Mike fork and Zensical supply the same null default. Since `0.0.65`, Mike's `version_selector` setting is supported; ANTA keeps the default enabled behavior.

## Temporary Workarounds

### Last Update Footer

Zensical `0.0.66` does not provide a native replacement for `mkdocs-git-revision-date-localized-plugin`; none is announced through `0.0.68`.

ANTA uses `_extensions.zensical_git_dates` from the local `anta-zensical-extensions` package instead. Contributors and CI install it explicitly with `-e tools/zensical_extensions` alongside the root `doc` dependency group, which supplies the Zensical pin for site builds. The extension reads the current page path from Zensical's rendering context and sets `page.meta.git_revision_date_localized`, which lets the upstream Zensical/Material `partials/source-file.html` render the normal footer.

This workaround is tied to [zensical/backlog#18](https://github.com/zensical/backlog/issues/18), which remains open as of October 5, 2026. Re-test it when upgrading Zensical. Before replacing it, also preserve ANTA's current date semantics: follow renames and ignore front-matter/license-only changes, rather than showing a new update date after a search-tag change.

The extension is outside `docs/` because Zensical copies non-page support files from `docs/` into the generated site. It lives under `tools/` instead of `.github/` so it is clearly local tooling and can be covered by the normal Python lint/type hooks.

### Custom Code Hook Shape

This helper is a Python-Markdown extension, not a MkDocs plugin.

Zensical accepts native plugin configuration for its supported replacements; this is not general support for arbitrary MkDocs plugin classes or lifecycle hooks. The `macros` shim supports page-rendering variables, macros, and filters. Its compatibility improvements in `0.0.65` and `0.0.68` do not supply the Git metadata replacement tracked above.

### Admonitions

ANTA documentation uses standard Python-Markdown admonition syntax such as `!!! note`, `!!! info`, `!!! warning`, and `!!! tip`.

ANTA does not use the old `gh-admonitions` MkDocs plugin. Zensical `0.0.67` adds a native `github-admonitions` replacement, but this is unavailable on the current pin and is not needed to improve existing pages. Keep standard admonitions for their richer types and custom titles; revisit GitHub alerts only for content intentionally shared between GitHub and the site.

### Obsidian Callouts

Since `0.0.62`, Zensical can enable Obsidian-style callouts through its `callouts` compatibility entry, which turns on `pymdownx.quotes` callout handling. ANTA has no Obsidian callout syntax, and its documentation already uses standard admonitions consistently. Enabling callouts would add a second authoring convention without adding a needed capability, so it remains disabled.

### Data-backed Tables

Zensical supports the `table-reader` compatibility entry for rendering structured table files. ANTA currently has no table-reader expressions or documentation-owned CSV, TSV, JSON, or YAML table sources. Most tables are small and prose-heavy; the longer security advisory support matrix is maintained directly in Markdown and has no separate structured source of truth. Moving the same manually maintained rows into another file would add indirection rather than prevent drift.

Reconsider table reader if ANTA later generates the advisory support matrix or another large reference table as a structured artifact. At that point, rendering the generated artifact would remove duplication instead of merely relocating it.

### GLightbox

ANTA uses Zensical's native `zensical.extensions.glightbox` Markdown extension instead of the external `mkdocs-glightbox` plugin.

The old MkDocs plugin accepted additional options such as `slide_effect`, `background`, `shadow`, `touchNavigation`, `loop`, and `effect`. Zensical's native extension does not implement all of those options, so ANTA uses its defaults:

```toml
[project.markdown_extensions]
"zensical.extensions.glightbox" = {}
```

The former width setting is intentionally not carried forward. Zensical turns configured dimensions into fixed GLightbox media-box dimensions, and GLightbox v3 applies `object-fit: cover`; together those settings crop tall terminal captures. Targeted rules in `extra.zensical.css` instead give the initial image a transparent `90vw` by `90vh` viewport and use `object-fit: contain`, preserving the image aspect ratio, using the available browser area, and keeping every edge visible.

The same rules preserve click-to-zoom with a consistent two-times viewport size for every image format. Using intrinsic dimensions is unreliable here: generated terminal SVGs only define a `viewBox`, while some raster screenshots are smaller than their fitted lightbox rendering.

GLightbox only attaches its zoom handler when an image's natural width exceeds its rendered width. That test skips viewBox-only SVGs and raster images enlarged by the initial fit. `glightbox-zoom.js` observes newly opened slides and adds equivalent click-to-zoom and drag-to-pan handling only when GLightbox did not attach its native `zoomable` class. Images accepted by GLightbox continue to use its native handler.

Zensical `0.0.66` bundles UI `0.0.33`, which fixes lost GLightbox styles after instant navigation. ANTA also has a defensive lightbox layout/style block in `extra.zensical.css`, beyond its aspect-ratio and zoom rules. Re-test that defensive block independently and remove only rules proven redundant. The upstream style fix does not establish that ANTA's tall-image fit or SVG zoom fallback is obsolete.

### CSS Overrides

`docs/stylesheets/extra.zensical.css` contains targeted `!important` overrides for Zensical header, search, and badge table styling. Re-test these visually when upgrading Zensical because upstream selector changes can silently change or bypass the custom styling.

### Snippets

`docs/snippets/api_tests_overview.md` was renamed to `docs/snippets/api_tests_overview.txt`.

Reason: Zensical renders Markdown files under `docs/` as pages even when the file is intended only for snippet inclusion. Keeping the snippet in `docs/snippets/` preserves the expected source organization, while the `.txt` suffix prevents it from becoming a rendered documentation page.

## Deliberately Out Of Scope

Historical deployed versions should not be rebuilt just to match the new Zensical UI. After this migration, it is acceptable for `/main/` to use the Zensical UI while older release folders keep the static MkDocs Material output they were originally deployed with.

## Validation

Local validation for the current version:

```bash
uv run --group doc zensical --version
uv run --group doc --with-editable tools/zensical_extensions zensical build --clean
uv run --group doc --with-editable tools/zensical_extensions zensical build --strict
uv run --group doc --with-editable tools/zensical_extensions mike deploy --ignore-remote-status --branch zensical-preview main
uv run --group doc --with-editable tools/zensical_extensions mike set-default --branch zensical-preview main
```

Expected result:

- `zensical --version` reports `0.0.66`
- clean build reports no issues
- strict build reports no issues
- no-push `mike deploy` builds successfully
- `mike set-default` lets `mike serve --branch zensical-preview` load `/` without a 404; `/main/` should also remain directly accessible

### Local multi-version preview

Use a throwaway local deploy branch to test the version selector, `stable` alias, and default redirect without touching `gh-pages`.

The following commands build three local versions using valid release identifiers accepted by `manage_doc_versions.py`:

- `main`
- `v0.0.0`
- `v0.0.1`, aliased as `stable`

```bash
uv run --group doc --with-editable tools/zensical_extensions mike deploy --ignore-remote-status --branch zensical-preview main
uv run --group doc --with-editable tools/zensical_extensions mike deploy --ignore-remote-status --branch zensical-preview v0.0.0
uv run --group doc --with-editable tools/zensical_extensions mike deploy --update-alias --ignore-remote-status --branch zensical-preview v0.0.1 stable
uv run --group doc --with-editable tools/zensical_extensions mike set-default --branch zensical-preview stable
uv run --group doc --with-editable tools/zensical_extensions mike serve --branch zensical-preview --dev-addr 127.0.0.1:8001
```

Expected result:

- `http://127.0.0.1:8001/` redirects to `/stable/`
- `/stable/` serves the `v0.0.1` content
- `/v0.0.0/`, `/v0.0.1/`, and `/main/` are directly accessible
- the version selector lists all three versions and shows `stable` as an alias for `v0.0.1`

To inspect the generated metadata without starting the server:

```bash
git show zensical-preview:versions.json
git show zensical-preview:index.html
```

Additional checks for the current pin:

- `/main/` is generated by `zensical-0.0.66`
- the page footer shows "Last update"
- `/main/snippets/api_tests_overview/` returns 404
- `/main/snippets/api_tests_overview.txt` is available as a raw snippet asset

The Mike commands above validate Mike alone, not the normalization/push wrapper. Before changing deployment, exercise `deploy_doc_version.sh` in a disposable repository with a local bare `origin`, seeded with representative `gh-pages` metadata. Check version ordering, stable alias movement, same-base prerelease removal, historical final-version preservation, and an identical redeploy. Do not run that wrapper against the real origin for a preview.

The active CI documentation gate is `zensical build --strict` on Python `3.11`; deployment jobs use Python `3.x`. A passing strict build does not verify browser interaction or version normalization. The commands here are a validation recipe, not a claim that this audit ran deployment or browser checks.

## Prioritized Improvements

### Guide-to-API object links (implemented)

Device/Inventory references in `docs/advanced_usages/as-python-lib.md` use autorefs identifiers to link to generated API objects. This keeps links tied to object identities rather than hard-coded page paths and heading anchors. Contributor guidance documents the authoring syntax and link validation.

API backlinks arrived in `0.0.65`, with theme styling added in `0.0.66`. The preview showed repeated "Referenced by" blocks on long API pages, and the maintainer chose to remove them. The global backlinks option and the custom rendering template are removed. Keep useful forward links from guides to API objects; enabling backlinks is not a planned follow-up.

### P1: Preserve existing page and heading links (available in 0.0.66)

Use the native redirects replacement whenever a docs cleanup renames a page or heading. `0.0.61` handles anchors, split pages, chains, and cycles. Configuration takes Markdown source paths:

```toml
# Example only: add entries for actual renames, not these placeholder paths.
[project.plugins.redirects.redirect_maps]
"guide.md#old-heading" = "guide.md#new-heading"
```

The contributor guide now documents page moves, heading renames, and section moves when splitting a page. For each actual move, verify the old page/fragment on `/main/` and a Mike release prefix, including a target hidden in a tab or details block. Do not add an empty redirect map or invent redirects without a moved destination.

### P1: Verify upstream UI fixes and reduce redundant CSS (available in 0.0.66)

Start with `docs/stylesheets/extra.zensical.css`, `glightbox-zoom.js`, and `mermaid-zoom.js`. Compare full-page loads and instant navigation between CLI screenshot pages and `api/class-diagram.md`, in both palettes and on mobile. Check uncropped tall SVG/PNG images, zoom/pan/close, Mermaid label colors and links, and the `/` search shortcut. Remove the defensive GLightbox styling only after the native styles load reliably; retain the independent fit/zoom behavior unless it also proves redundant. Keep custom Mermaid zoom: respecting label colors is not a native fullscreen/zoom replacement.

The separate `fix/docs-glightbox-styles` investigation confirms that [UI fix `49cc6dab`](https://github.com/zensical/ui/commit/49cc6dab5657558b0b9a5218767e3c003430fdc7) for [issue #243](https://github.com/zensical/ui/issues/243) is included in the current `0.0.66` bundle. It preserves stylesheet loading across instant-navigation mounts. No runtime CSS or JavaScript is removed without a browser comparison. The native loader still depends on CDN assets; local defensive CSS alone does not provide offline operation.

### P1: Make the post-0.0.66 upgrade reproducible

Prefer qualifying the latest release, `0.0.68`, for its search-result navigation and accessibility fixes rather than updating just for media plugins. Update all three pins together (`pyproject.toml` and the two pre-commit `additional_dependencies`), and require Python >=3.11 for documentation tooling. ANTA's library minimum remains >=3.10.

Python `3.10` reached end of life on October 1, 2026, according to [PEP 619](https://peps.python.org/pep-0619/). Zensical's [October 5 support-removal commit](https://github.com/zensical/zensical/commit/4559ba85df8266e1f0db5cb2466211d8b37a75f7) does not state its rationale, but raises both the package and compiled extension minimum to `3.11` and removes a date-parsing compatibility workaround. Treat this as an actual tooling compatibility boundary.

For uv, declare the narrower [group Python requirement](https://docs.astral.sh/uv/concepts/projects/dependencies/#group-requires-python) so universal dependency resolution does not try to install Zensical `0.0.68` on Python 3.10:

```toml
[tool.uv.dependency-groups]
doc = { requires-python = ">=3.11" }
```

Also document the minimum in contributor instructions and ensure the two Python hook environments use Python >=3.11. The docs CI job already uses `3.11`; deployment jobs use `3.x`. Verify package/test workflows still support Python 3.10 independently of docs installation. Re-run the strict build, Git footer check, object inventory checks, and local multi-version validation. Check keyboard skip links, overlay labels, and instant navigation from search results in the browser. Adding audio/video is optional and requires a real content need.

### P2: Offer rendered Markdown and Copy as Markdown (requires >=0.0.67)

Pilot the native `llmstxt` plugin for guides and selected API pages. It exports rendered content, including snippets and mkdocstrings output, so readers and tools can use the documentation without resolving ANTA's source-only `:::` and snippet directives. Add `content.action.copy` to the existing theme feature array as well: the [copy button requires an exported Markdown URL](https://github.com/zensical/ui/blob/v0.0.34/src/partials/actions.html), so that feature alone is insufficient.

```toml
[project.plugins.llmstxt]
markdown_description = "ANTA guides and Python API reference"

[project.plugins.llmstxt.sections]
Guides = ["getting-started.md", "usage-inventory-catalog.md", "advanced_usages/as-python-lib.md"]
API = ["api/device.md", "api/inventory.md"]
```

Check exported examples, admonitions, cross-references, and version-aware URLs. In particular, ANTA's custom test/input templates render their own source `<details>`: ensure exports omit implementation listings while preserving catalog examples and Expected Results. Upstream tests cover standard mkdocstrings source removal, not ANTA's overrides. Offer per-page Markdown first; add `full_output = "llms-full.txt"` only if the combined size and version scope are useful. Keep `main` and release exports distinct and preserve the deployment root redirect.

### P2: Improve previews when people share documentation links (requires >=0.0.67)

Enable the native `social` plugin in a small trial with branded cards for getting started, inventory/catalog, and advisory usage. Give those pages useful titles and descriptions. Start from the bundled layout; verify generated Open Graph/Twitter metadata and image URLs under both `/main/` and release prefixes. Check font/image dependencies and cache behavior in CI before enabling site-wide generation. This needs no external MkDocs social package.

### P2: Evaluate API generation without losing curated content (available in 0.0.66)

Trial either `[project.plugins.mkdocs-autoapi]` or `[project.plugins.api-autonav]` on a small public package in a separate output section. These are the user-facing configuration keys; Zensical's internal normalized names differ. Exclude private modules explicitly and compare the discovered public modules with existing reference coverage. Do not enable both generators together or generate duplicate pages for objects already documented.

ANTA's test pages combine tests and input models, compatibility notes, per-page filters, and custom templates. Preserve these pages and their current URLs. Adopt generation only where it demonstrably removes boilerplate without changing the intended public surface, navigation order, or object-link destinations. For now, a coverage audit using generated candidates is more valuable than replacing the whole hand-maintained API navigation.

### P2: Improve contributor feedback and search discovery (mostly available now)

- Exercise the `0.0.63` snippet rebuild fix on root `README.md`, one CLI snippet, an `examples/` inclusion, and `api/class-diagram.mmd` during `zensical serve`. Add a watched source path only if an included file fails to trigger a rebuild; dependencies should be tracked by the snippets implementation.
- Review existing search tags with tasks such as "BGP peer health", "inventory from Ansible", and "JSON report". They already exist in page front matter; native search is enabled. Improve missing labels/headings before adding another tag index.
- Pilot `navigation.instant.preview` on a few cross-reference links after measuring usability on the long generated API pages. This is an existing deferred idea, not a feature introduced after `0.0.60`. Check keyboard/touch behavior and interference with the custom overlays before enabling it globally.
- Inspect `sitemap.xml` after the `0.0.66` all-published-pages fix. Navigation membership does not make a page unpublished; confirm every indexed page is intended and assess `main`-only canonical destinations.
- After upgrading, trial `[project.plugins.exclude]` for documentation tooling/template assets that do not need public copies. `0.0.63` already excludes dotfiles, but ordinary source files are a separate case. Preserve snippet reads and existing raw-asset contracts; keep `api_tests_overview.txt` until an exclusion-based alternative has been validated.

### Defer until there is a content owner or source of truth

- **Blog/RSS:** native support arrived in `0.0.64`/`0.0.65`. Use it for maintained tutorials or release articles only if someone owns publication. The Git footer helper writes a display string, not RSS creation/update metadata; do not assume it supplies feed dates. Test versioned feed URLs and avoid duplicate entries across releases.
- **Table reader:** already available at the `0.0.60` baseline. Adopt for a generated advisory/support dataset, not merely to move manually maintained Markdown rows into another file.
- **GitHub alerts/Obsidian callouts:** keep the current admonition convention unless shared-source authoring has a concrete benefit.
- **Audio/video:** `0.0.68` supports these natively, but ANTA's current terminal assets do not justify adding media solely because the plugins exist.

## Acceptance Criteria For Follow-up Changes

### Actionable backlog from discussion items 4–17

The numbers below match the maintainer discussion. These tasks are recorded for later implementation, rather than enabled by this branch. Item 3 (GLightbox) is investigated separately on `fix/docs-glightbox-styles`.

| Item | Action | Completion criteria |
| --- | --- | --- |
| 4 — Upgrade qualification | Qualify Zensical `0.0.68`; update all three pins, document Python >=3.11 for docs, declare the uv group requirement, and select compatible Python hook environments. | Clean/cached strict builds, working Git dates and object inventory, versioned preview, keyboard/accessibility checks, and preserved ANTA Python 3.10 package/test support. |
| 5 — Markdown exports | Pilot `llmstxt` on selected guides and API pages; add `content.action.copy` to the existing feature list after upgrading. | Exported snippets, signatures, examples, Expected Results, and links are usable; ANTA's custom source listings are handled intentionally; copied content belongs to the selected documentation version. |
| 6 — Social cards | Trial native social cards with useful titles/descriptions on Getting Started, inventory/catalog, and advisory usage. | Correct metadata/image URLs for `main` and a release; understood font/image requirements and build/cache cost. |
| 7 — API generation | Trial one API generator as a coverage audit for a small public package. | Missing public coverage is identified; private modules are excluded; adoption preserves curated test/input pages, existing URLs, navigation order, and object destinations. |
| 8 — Snippet rebuilds | Check live updates for root README, a CLI snippet, an example, and the class diagram. Add watched paths only for observed gaps. | Preview updates without restarting the server or editing the including page. |
| 9 — Search | Review results for realistic tasks such as BGP peer health, inventory from Ansible, and JSON reports; improve headings, descriptions, or tags where necessary. | The intended guide/test and relevant section are discoverable with the chosen user wording. |
| 10 — Instant previews | Pilot previews for representative guide/API links using the existing feature. | Useful context on long API pages; workable keyboard/touch interaction; no interference with custom overlays. |
| 11 — Sitemap/canonicals | Audit generated sitemap membership and canonical targets, especially pages introduced only on `main`. | Every listed page is intended; missing stable counterparts are identified and an appropriate canonical policy is chosen. |
| 12 — Asset exclusions | After upgrading, inspect generated assets and exclude specific documentation build-only sources using the native replacement. | Images, scripts used by the site, downloads, snippet reads, and intentional raw assets remain functional. |
| 17 — Existing helpers | Re-check native Git metadata support at each upgrade and retain the current helper until its date semantics are covered. Validate version normalization when Mike/deployment changes. | Renames and metadata/license-only edits preserve footer semantics; version order, stable movement, prerelease cleanup, and historical final builds remain correct. |

Items 13–16 remain conditional: blog/RSS needs a publication owner; table reader needs an authoritative structured dataset; alternative callout syntax needs shared-source authoring; audio/video needs a specific learning use case. Revisit the corresponding proposal only when its condition exists.

### Validation requirements

- Run changed-file pre-commit checks first, then `pre-commit run --all-files` for final validation.
- Build affected documentation with the pinned version using `--clean --strict`; repeat without cleaning when evaluating cached references, inventories, or generated pages.
- Validate the interaction affected by a change in both palettes, including instant navigation and a version-prefixed site. A plan-only edit does not require rebuilding the site.
- For deployment changes, include the existing `tests/docs/test_manage_doc_versions.py` coverage and the disposable-origin wrapper check above.
- Retain the Git footer extension until native support matches the required semantics. Track [backlog#18](https://github.com/zensical/backlog/issues/18) at each upgrade.
