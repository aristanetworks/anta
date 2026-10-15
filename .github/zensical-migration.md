<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Zensical Documentation Plan

**Baseline:** `upstream/main` at `11d925e4`, Zensical `0.0.68`
**PR:** [#1809](https://github.com/aristanetworks/anta/pull/1809), `docs/zensical-improvements`
**Updated:** October 15, 2026

The MkDocs Material migration is complete. PR #1809 is rebased onto `main` and retains ANTA's lightbox layout and zoom behavior, fixes cumulative slow-drag detection, and documents redirects and API object links. This plan separates settled decisions from optional follow-ups. Feature experiments remain evidence for later work, not enabled configuration.

## Current baseline

- `pyproject.toml` and both Pylint/Pyright pre-commit environments pin `zensical==0.0.68`.
- Zensical uses `zensical.toml`, native search, instant navigation, linked content tabs, code copying, `mkdocstrings`, GLightbox, and custom Mermaid zoom.
- Documentation tooling requires Python >=3.11, independently of ANTA's library support. The `doc` dependency group declares that minimum for uv resolution; the contributor guide documents it. Docs CI uses Python 3.11 and deployment selects Python 3.x.
- The local extension is installed with `-e tools/zensical_extensions`. MkDocs and autorefs remain dependencies of `mkdocstrings`; site commands use Zensical.
- Versioned deployment uses the compatible Mike fork at `2d4ad799442f4592db8ad53b179bfb33db8c69ac` and ANTA's deployment/normalization scripts.

[Zensical 0.0.68](https://github.com/zensical/zensical/releases/tag/v0.0.68) includes native audio/video support, closer macros compatibility, and UI 0.0.35 search-result instant navigation and accessibility fixes. It requires Python >=3.11. Features inherited from earlier releases include redirects, snippet-dependent rebuilds, blog/RSS, API generators, social cards, Markdown exports, and asset exclusions. Availability does not imply adoption.

## Decisions

1. **Keep API backlinks disabled.** The preview's repeated “Referenced by” blocks cluttered long API pages. Keep forward guide-to-object links through autorefs instead. The Python-library guide now uses object references for Device, Inventory, Command, Test, and TestStatus links.
2. **Preserve published links when content moves.** Follow `docs/contribution.md` for docs-relative page/fragment redirects and update repository links. Add mappings only for actual moves. Check old URLs within the selected documentation version; historical builds acquire new mappings only when rebuilt.
3. **Retain the lightbox layout, image fitting, and two-times zoom.** The native-only experiment made images too small and lost useful zoom. Keep the custom fallback for images without GLightbox's `zoomable` class and the cumulative slow-drag fix. Browser QA remains open; a Node handler harness does not establish smoothness or touch quality.
4. **Retain custom Mermaid zoom.** Upstream label-color fixes do not replace ANTA's fullscreen/zoom interaction. Preserve diagram links and palette behavior. Initialize zoom controls when Zensical inserts the asynchronously rendered diagram, including after instant navigation; do not attach them to the temporary source element.
5. **Keep Markdown export and Copy as Markdown disabled pending link fixes.** Earlier experiments lost API autorefs links and produced links to unselected Markdown files. A passing strict build does not establish usable exports. Do not replace authored autorefs with hard-coded paths to conceal exporter defects.
6. **Keep curated API navigation and standard admonitions.** API generation is a coverage-audit candidate, not a replacement for curated test/input pages. Consider GitHub alerts (`gh-admonitions`) or Obsidian callouts (`callouts`) only for a concrete shared-source need.
7. **Retain the Git date extension and Mike deployment helpers.** Replacements must preserve rename-aware dates, ignored metadata/license-only edits, version order, stable aliases, same-base prerelease cleanup, and historical final builds. Recheck [Git metadata backlog #18](https://github.com/zensical/backlog/issues/18) at upgrades.
8. **Keep feature adoption separate from version updates.** This PR uses 0.0.68 supplied by `main`. Social cards, exports, API generators, instant previews, exclusions, blog/RSS, table reader, and media remain optional. Update all three version pins together in any future upgrade and qualify documentation tooling separately from library Python support.

## Actions to consider

The original discussion item numbers are retained for traceability. Only the browser acceptance check is outstanding for this PR; other actions are follow-up candidates.

| Item | Priority and action | Evidence required before completion or adoption |
| --- | --- | --- |
| 3 — Lightbox QA | **Before merge:** test the retained lightbox and drag fix on CLI screenshot pages and `api/class-diagram.md`. | Check SVG/raster images and both native `zoomable` and fallback `anta-zoomable` paths: uncropped fit, click zoom, slow/fast and repeated pans, release without zoom-out, deliberate subsequent click, cancellation, close/reopen, and slide changes. Test both palettes, instant navigation, a version prefix, and touch. Check Mermaid zoom/links too. Change behavior only for a reproduced defect. |
| 4 — Upgrade qualification | **Next audit:** qualify the inherited 0.0.68 UI and tooling changes; consider a later version only for a demonstrated benefit. | Check search-result navigation, `/` search, keyboard skip links/labels, Git dates, object inventory, and local versioned output. Keep hook interpreters compatible with documentation dependencies. Preserve independent library/test support. Do not assume newer releases fix export links. |
| 8 — Snippet rebuilds | **Audit:** edit representative included sources during `zensical serve`. | Root README, one CLI snippet, an included example, and `api/class-diagram.mmd` update their dependent pages without a restart or edits to the including page. Restore trial edits; add watch paths only for observed gaps. |
| 9 — Search | **Audit:** try “BGP peer health”, “inventory from Ansible”, and “JSON report”. | Record result quality and destinations; improve accurate headings, descriptions, or tags only where results are weak. |
| 11 — Sitemap/canonicals | **Audit:** inspect generated sitemap entries and canonicals for pages present only on `main`. | Every indexed page is intentional; canonical destinations exist or an explicit policy handles missing stable counterparts. Preserve historical releases. |
| 17 — Existing helpers | **At upgrades:** recheck native Git metadata and versioning support. | Match existing date/version contracts before replacing helpers. Deployment changes require `tests/docs/test_manage_doc_versions.py` and a disposable-origin wrapper check, including repeated deploys. |
| 5 — Markdown exports | **Blocked pilot:** reproduce the earlier export link gaps on 0.0.68 before adoption. | Preserve API object links and all local Markdown destinations. Omit source listings narrowly while retaining examples, signatures, tables, catalog YAML, and Expected Results. Decide image policy; test actual clipboard content, instant navigation, and Mike version prefixes. Enable `llmstxt` and `content.action.copy` together only after these checks. |
| 6 — Social cards | **Pilot:** trial native `social` on Getting Started, inventory/catalog, and advisory usage. | Inspect branded images and metadata, main/release asset URLs, fonts, fresh/cached builds, and build cost. Adopt only if shared-link previews improve. |
| 7 — API generation | **Pilot:** use one of `mkdocs-autoapi` or `api-autonav` to audit a small public package. | Identify coverage gaps; exclude private modules and duplicate objects. Preserve curated test/input content, URLs, navigation order, and object destinations. |
| 10 — Instant previews | **Pilot:** trial `navigation.instant.preview` on representative guide/API links. | Useful context without clutter; working keyboard/touch access, both palettes, and no conflict with GLightbox/Mermaid overlays. |
| 12 — Asset exclusions | **Pilot:** inventory output and trial narrow `exclude` patterns for build-only scripts/templates. | Compare clean/cached output. Preserve source reads, intended pages, raw snippet TXT, downloads, images, theme assets, and site scripts. Avoid broad wildcards. |
| 13 — Blog/RSS | **Conditional:** revisit when an owner commits to maintained articles. | Define feed dates, versioned URLs, and duplicate-entry policy. The Git footer display string is not feed timestamp metadata. |
| 14 — Table reader | **Conditional:** revisit for an authoritative structured reference dataset. | Remove duplicate maintenance while preserving readable tables and links. Moving manual rows into another file alone is insufficient. |
| 15 — Alternative callouts | **Conditional:** revisit for Markdown shared with GitHub or Obsidian. | Demonstrate correct rendering in both destinations and document when each syntax is appropriate. |
| 16 — Audio/video | **Conditional:** use the available native support for a specific learning need. | Provide accessible text/captions, working versioned playback/assets, and acceptable page/build cost. Terminal screenshots alone do not establish a need for video. |

## Earlier experiments to preserve

These measurements came from temporary **Zensical 0.0.67** configurations recorded on October 9. They are not 0.0.68 acceptance results, and their trial changes are not enabled in production.

| Experiment | Result and implication |
| --- | --- |
| Selected Markdown exports | Six exports linked to five distinct unselected Markdown files whose HTML pages existed. Example: exporting Getting Started without Installation produced a missing `requirements-and-installation/index.md` target. |
| All-page exports | 77 exports (598,303 bytes) had no missing local Markdown targets in that build, but API autorefs links still became plain text. Compare Device/Inventory links in HTML against exported Markdown when retesting. |
| Custom source-wrapper cleanup | Adding `mkdocstrings-source` only to the two custom source wrappers in `docs/templates/python/material/class.html.jinja` removed 33 BGP implementation-source headings and reduced the export from 159,076 to 48,351 bytes. All 24 Examples and 24 Expected Results sections remained, as did HTML source details. This is a candidate change after export link blockers are resolved. |
| Image cleanup | Default cleanup removed images. `autoclean = false` preserved five image references but added 139 heading permalink markers. Image policy needs a deliberate choice. |
| Export version prefixes | Explicit main/release `site_url` trials produced matching export URLs. Actual Mike integration and browser clipboard behavior were not verified. |
| Narrow asset exclusions | A strict-build pilot excluded `scripts/**` and `templates/**` copies while retaining API template rendering and `snippets/api_tests_overview.txt`. Public asset contracts still need an audit before adoption. |
| Fallback drag handler | A temporary Node harness reproduced the original slow-drag zoom-out defect and passed the revised handler, including repeated gestures, cancellation, and pointer filtering. Browser interaction remains to be checked. |

GLightbox's native loader fetches JavaScript and CSS from `https://unpkg.com/glightbox@3/`. Defensive local CSS can style an existing overlay; it does not provide complete offline operation or initialize the library after an asset-loading failure. Any CSS reduction needs browser evidence that image fitting and zoom remain usable.

## Validation and local preview

### Recorded results

- The maintainer [reported successful local browser testing](https://github.com/aristanetworks/anta/pull/1809#discussion_r4276426545), and CodeRabbit resolved the manual-validation thread. That report does not enumerate browsers, touch devices, palettes, or version prefixes; do not infer complete coverage of those scenarios.
- A subsequent maintainer check found the class-diagram Zoom button missing after instant navigation but present after refresh. The helper now observes insertion of the rendered diagram instead of relying only on its initial timed checks.
- A temporary DOM/MutationObserver regression harness reproduced missing controls with the old helper when rendering completed after the initial 100 ms. The revised helper passed delayed rendering, temporary source replacement, repeated navigation/initialization, and unrelated DOM updates without duplicate controls or listeners. This is automated DOM coverage, not browser acceptance of the fix.
- A clean strict build passed with Zensical 0.0.68, and changed-file and all-files pre-commit checks passed. The rendered API link audit found no missing authored API pages or fragments. Version-selector links into `stable/` need a multi-version preview, which the standalone build does not provide.

### Reproduce locally

Run from the repository root using Python >=3.11 and the pinned dependency group:

```bash
uv run --group doc --with-editable tools/zensical_extensions zensical --version
uv run --group doc --with-editable tools/zensical_extensions zensical build --clean --strict
uv run --group doc --with-editable tools/zensical_extensions zensical serve --dev-addr=127.0.0.1:8000
```

- Verify the executable reports 0.0.68. Check rendered guide-to-API destinations, the Git date footer, `objects.inv`, and absence of backlink blocks.
- Run changed-file pre-commit checks first and all-files checks for final validation. Review any hygiene changes before accepting them.
- Record browser results against item 3 rather than treating a build or event harness as browser acceptance.
- For URL/version changes, use a disposable local Mike main/release preview. Check direct entry and instant navigation, including targets inside details or tabs.
- Run deployment wrapper experiments only in a disposable repository with a local bare origin. The real wrapper publishes to `origin/gh-pages`; it is not a local preview command.
