<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Zensical Documentation Plan

**Baseline:** `upstream/main` at `855d66c1` (merged #1809), Zensical `0.0.68`
**Migration PR:** [#1809](https://github.com/aristanetworks/anta/pull/1809) (merged); follow-up outcomes are tracked below.
**Updated:** October 16, 2026

The MkDocs Material migration is complete. Merged PR #1809 retains ANTA's lightbox layout and zoom behavior, fixes cumulative slow-drag detection, and documents redirects and API object links. This plan records current decisions, why they were made, when to revisit them, and proposed follow-up PRs. Feature experiments remain evidence for later work, not enabled configuration.

## Current baseline

- `pyproject.toml` and both Pylint/Pyright pre-commit environments pin `zensical==0.0.68`.
- Zensical uses `zensical.toml`, native search, instant navigation, linked content tabs, code copying, `mkdocstrings`, GLightbox, and custom Mermaid zoom.
- Documentation tooling requires Python >=3.11, independently of ANTA's library support. The `doc` dependency group declares that minimum for uv resolution; the contributor guide documents it. Docs CI uses Python 3.11 and deployment selects Python 3.x.
- The local extension is installed with `-e tools/zensical_extensions`. MkDocs and autorefs remain dependencies of `mkdocstrings`; site commands use Zensical.
- Versioned deployment uses the compatible Mike fork at `2d4ad799442f4592db8ad53b179bfb33db8c69ac` and ANTA's deployment/normalization scripts.

[Zensical 0.0.68](https://github.com/zensical/zensical/releases/tag/v0.0.68) includes native audio/video support, closer macros compatibility, and UI 0.0.35 search-result instant navigation and accessibility fixes. It requires Python >=3.11. Features inherited from earlier releases include redirects, snippet-dependent rebuilds, blog/RSS, API generators, social cards, Markdown exports, and asset exclusions. Availability does not imply adoption.

## Decision register

This register is the durable record of migration choices, including features deliberately left disabled. **Adopted** means an agreed convention is in effect; **retained** means the current implementation remains the default; **deferred** means no adoption is planned until the revisit condition is met; **blocked** means a demonstrated problem prevents adoption. None of these statuses means a feature is rejected forever.

The entries below record migration decisions and follow-up outcomes as of October 16, 2026. Their IDs remain stable across follow-up PRs. Each entry records the reason and the evidence needed to reconsider it, so a dependency update alone does not silently reverse a choice.

| ID | Decision and status | Reason / evidence | Revisit when |
| --- | --- | --- | --- |
| D01 | **Deferred:** API backlinks remain disabled for now. Keep forward links through autorefs; F01 extends this convention to the remaining authored object links. | PR #1809 preview showed repeated “Referenced by” blocks cluttering long API pages; maintainer feedback favored removing them. | Upstream offers selective/collapsed backlinks, or readers identify a concrete reverse-navigation need. Compare a small preview against the current API pages and obtain maintainer feedback before enabling them. |
| D02 | **Adopted:** preserve published page and heading URLs with native redirects when content moves. | Contributor guidance in PR #1809 protects external links/bookmarks without placeholder redirect maps. Historical builds change only when rebuilt. | A real page/heading move requires a mapping, or versioned preview exposes incorrect fragment handling. Verify direct entry and instant navigation within the selected version. |
| D03 | **Retained:** custom lightbox layout, aspect-preserving fit, and two-times zoom. | The native-only experiment made images too small and lost useful zoom. Native GLightbox and the ANTA fallback cover different images. Slow-drag logic was fixed in PR #1809; full browser coverage is not claimed. | Native behavior demonstrably covers tall SVG/raster fitting, zoom, pan, touch, palettes, and navigation. Reduce CSS/helper code only after a side-by-side browser comparison. |
| D04 | **Retained:** custom Mermaid fullscreen/zoom and asynchronous initialization. | Upstream label-color fixes do not replace these interactions. The reported missing Zoom button after instant navigation required observing the rendered element instead of the temporary source block. | A native replacement covers fullscreen, scale controls, panning, links, keyboard/focus, palettes, and instant navigation, with regression evidence. |
| D05 | **Blocked:** rendered Markdown exports and Copy as Markdown remain disabled. | The 0.0.67 experiments lost API autorefs links and created missing Markdown destinations; cleanup also affected images. Measurements and reproduction details are preserved below. | A runtime retest on the target version preserves object links and complete destinations. Decide image/source-listing policy and verify clipboard contents under real Mike prefixes before adoption. Do not hard-code authored API links to conceal exporter defects. |
| D06 | **Retained:** curated API pages/navigation; F01 changes object references while preserving overview-page links. | ANTA's test/input pages include pairing, examples, filters, compatibility notes, and custom templates. Wholesale generation could lose content or duplicate objects. | A small coverage audit with one generator finds missing public objects or demonstrably removes boilerplate while preserving URLs, navigation, object targets, and curated content. |
| D07 | **Retained:** standard Python-Markdown admonitions. GitHub alerts (`gh-admonitions`) and Obsidian callouts (`callouts`) remain deferred. | No identified shared-source need justifies another authoring convention. | Actual Markdown needs to render in GitHub or Obsidian as well as the site. Compare both renderers and document the resulting convention. |
| D08 | **Retained:** local Git date extension. | The footer must follow renames and ignore metadata/license-only edits. Its display string is not RSS timestamp metadata. Native support is tracked in [backlog #18](https://github.com/zensical/backlog/issues/18). | Native support can satisfy those date semantics. Check at Zensical upgrades and compare representative pages before replacing the extension. |
| D09 | **Retained:** compatible Mike fork and deployment/normalization helpers. | They preserve version order, stable aliases, same-base prerelease cleanup, and historical final builds. A strict site build does not test deployment behavior. | Native/upstream alternatives satisfy these contracts in a disposable-origin integration test, including identical redeploys. Never use the production publishing wrapper for a preview. |
| D10 | **Adopted:** documentation tooling and library Python support are independent; dependency updates do not enable features automatically. | Zensical 0.0.68 requires Python >=3.11. The root doc group and both hook environments share its pin. | Every documentation-tooling upgrade: align all three pins and check group/interpreter constraints, builds, inventories, and browser behavior without silently changing library support. |
| D11 | **Deferred:** social cards. | Native support is available, but branding, fonts/assets, caching, versioned URLs, and build cost need evaluation. | A small branded preview demonstrates useful shared-link presentation at acceptable cost. |
| D12 | **Deferred:** instant link previews. | They may help long API pages but can add clutter and interfere with overlays. | A representative guide/API pilot improves navigation and works with keyboard, touch, palettes, and overlays. |
| D13 | **Deferred:** build-only asset exclusions. | A temporary narrow pilot worked, but exclusions can filter source documents and effective resources, including theme assets. | An output inventory identifies unnecessary public copies and a narrow comparison proves source reads, raw snippets, downloads, images, templates, and site assets survive. |
| D14 | **Deferred:** blog and RSS. | There is no publication owner or agreed feed date/version policy. | A named owner commits to maintained articles and defines dates, versioned URLs, and duplicate-entry policy. |
| D15 | **Deferred:** table reader. | Moving manually maintained rows into another file alone does not remove drift. | An authoritative structured dataset can generate a reference table with preserved links and a single maintenance source. |
| D16 | **Deferred:** audio/video. | Available support alone does not establish a learning need; media adds accessibility and asset costs. | A concrete explanation benefits from media with accessible text/captions, versioned playback, and acceptable page/build cost. |

### Updating a decision

Every follow-up PR updates this file alongside its implementation or investigation:

1. Reference the affected decision IDs and follow-up ID in the PR description.
2. Record the tested Zensical version, evidence, limitations, and outcome here; a successful build is not browser or deployment acceptance.
3. For a changed decision, retain its ID and earlier reason in a dated entry in the history below, then update the current status/revisit condition. A closed pilot can leave a feature deferred or blocked.
4. Replace the proposed follow-up's status with its actual PR link and outcome. Do not delete completed or declined proposals; keep enough history to explain why.

### Decision history

| Recorded | Decisions | Outcome and evidence |
| --- | --- | --- |
| 2026-10-16 | D01/D06 — F01 | Replaced 47 authored API object links with autorefs, retaining two overview-page links. A clean strict Zensical 0.0.68 build passed; rendered link destinations were checked for existing pages/fragments. Backlinks remain deferred and API generation remains a separate audit. |
| 2026-10-15 | D01–D16 | Consolidated the choices and earlier experiments from PR #1809 into this register. In particular, backlinks remain deferred because of preview clutter; this is a current choice that can be revisited, not a permanent rejection. |

## Follow-up PR plan

The table tracks proposed scopes and completed outcomes; it is not a commitment to enable every feature. Finish PR #1809's remaining browser confirmation before treating its interaction fixes as fully qualified. PR #1809 has merged; F01–F03 can proceed; the independent audits and pilots can follow without stacking unrelated changes into the same PR.

| ID / proposed PR | Status and dependencies | Scope | Completion criteria / decision updates |
| --- | --- | --- | --- |
| F01 — Finish API object references | **Implemented; PR pending.** Based on merged #1809. | Converted 46 of the 48 hard-coded API links across `custom-tests.md`, `caching.md`, `usage-inventory-catalog.md`, `reports/anta.md`, and `cli/nrfu.md`, plus one object link in the shared test-overview snippet (47 total). The inventory and test overview links remain normal page links. Reporter implementation links now target their public classes; the custom-types link targets its module. | Clean strict build passed on Zensical 0.0.68. Rendered object destinations resolve to existing pages/fragments, including the dedicated full `AntaTest` API page rather than partial inline documentation. D01/D06 are retained: backlinks remain deferred and curated API pages remain in place. This improves link consistency and resilience; it does not qualify browser interactions or versioned deployment. |
| F02 — Browser regression coverage for diagrams and images | **Proposed; high priority.** After #1809; independent of F01. | Add a small repeatable browser suite for class-diagram instant navigation and lightbox gestures, using a documented browser-test command and fixtures. Preserve a short manual touch checklist for device behavior automation cannot establish. | Reproduce the former missing Zoom button and slow-drag zoom-out defects against the prior helpers; pass with fixes. Cover delayed rendering, navigation away/back, zoom/pan/close, keyboard/focus, SVG/raster paths, and both palettes. Record browser/version and actual touch/emulation coverage. Update D03/D04 and distinguish automated evidence from perceived smoothness. |
| F03 — Versioned URLs, sitemap, and canonicals | **Proposed; high priority.** After #1809; independent of F01/F02. | Build a disposable local Mike main/release preview and audit version selection, direct fragments, instant navigation, sitemap membership, and main-only canonical destinations. | Identify intended published pages; verify selected-version URLs, stable destinations, footer, inventory, and deep links into details/tabs. Define any missing-counterpart policy explicitly. Update D02/D08/D09; if changing deployment, run `tests/docs/test_manage_doc_versions.py` and a disposable-origin wrapper check. |
| F04 — Live snippet rebuild qualification | **Proposed audit.** After #1809. | During `zensical serve`, change root README, a CLI snippet, an included example, and the Mermaid source. Add watch paths only for reproduced gaps. | Each dependent page updates without restarting or touching the including page; restore trial edits and record results. Fix only observed watcher failures and update the baseline evidence for D10. |
| F05 — Search and accessibility qualification | **Proposed audit.** After #1809. | Check BGP peer health, inventory from Ansible, and JSON report queries; qualify inherited search-result instant navigation, `/` search, skip links, and overlay labels. | Record query/destination and keyboard results. Improve accurate headings, descriptions, tags, or demonstrated UI defects only. Update D10 with browser evidence rather than enabling another search feature. |
| F06 — Markdown export blocker investigation | **Blocked adoption; investigation can run independently.** After #1809. | Retest lost autorefs, unselected Markdown targets, cleanup/images, and source-wrapper behavior on the target pin. Prepare minimal upstream reproductions where defects remain. | Record reproductions and tested version under D05. If still broken, close the investigation with adoption blocked. If fixed, propose a separate enablement PR with destination/content audits and real versioned clipboard checks; do not mix exporter workarounds into F01. |
| F07 — Narrow asset exclusions | **Optional pilot.** Prefer after F03 establishes public asset contracts. | Inventory output and trial exclusions for unnecessary script/template source copies. | Compare clean/cached output; preserve custom rendering, source reads, intended pages, raw snippet TXT, downloads, images, and site/theme assets under version prefixes. Update D13 whether adopted or declined. |
| F08 — API coverage audit with one generator | **Optional audit.** Prefer after F01 establishes consistent object links. | Trial either `mkdocs-autoapi` or `api-autonav` for a small public package in isolated output. | Identify missing public coverage without exposing private objects or duplicating destinations. Preserve curated test/input content, URLs, and navigation. Update D06; wholesale generation is not the default outcome. |
| F09 — Social-card pilot | **Optional pilot.** Independent; reuse F03's versioned preview. | Trial native `social` on Getting Started, inventory/catalog, and advisory usage. | Inspect actual branded images and metadata, main/release URLs, fonts, fresh/cached builds, and cost. Record adoption or deferral under D11. |
| F10 — Instant-preview pilot | **Optional pilot.** Prefer after F02 provides overlay regression coverage. | Trial `navigation.instant.preview` on representative guide/API links. | Assess useful context, clutter, keyboard/touch behavior, palettes, and overlay conflicts. Update D12 whether kept or declined. |

### Conditional follow-ups

- **Backlinks (D01):** open a focused pilot only when its revisit condition is met. Do not bundle them into F01, F08, or a dependency upgrade.
- **Git dates / deployment (D08/D09):** recheck native support during upgrades; open a replacement PR only after contract parity is demonstrated.
- **Shared callouts, blog/RSS, table reader, and media (D07/D14–D16):** keep these in the register until their authoring, ownership, dataset, or learning-use condition exists. An available plugin is not sufficient justification for an implementation PR.

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
- Record browser results against D03/D04 and follow-up F02 rather than treating a build or event harness as browser acceptance.
- For URL/version changes, use a disposable local Mike main/release preview. Check direct entry and instant navigation, including targets inside details or tabs.
- Run deployment wrapper experiments only in a disposable repository with a local bare origin. The real wrapper publishes to `origin/gh-pages`; it is not a local preview command.
