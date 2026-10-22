<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Zensical Documentation Plan

**Source baseline:** `main` at `97338a6d`, merged into #1828 on October 21, 2026 (includes merged #1809 and Zensical 0.0.69)
**Documentation tooling:** Zensical `0.0.69` (already on `main`)
**Migration PR:** [#1809](https://github.com/aristanetworks/anta/pull/1809) (merged); follow-up outcomes are tracked below.
**Updated:** October 22, 2026

The MkDocs Material migration is complete. Merged PR #1809 retains ANTA's lightbox layout and zoom behavior, fixes cumulative slow-drag detection, and documents redirects and API object links. This plan records current decisions, why they were made, when to revisit them, and completed work. Feature experiments remain evidence for later work, not enabled configuration.

## Current baseline

- `pyproject.toml` and both Pylint/Pyright pre-commit environments pin `zensical==0.0.69`.
- Zensical uses `zensical.toml`, native search, instant navigation, linked content tabs, code copying, `mkdocstrings`, GLightbox, and custom Mermaid zoom.
- Documentation tooling requires Python >=3.11, independently of ANTA's library support. The `doc` dependency group declares that minimum for uv resolution; the contributor guide documents it. Docs CI uses Python 3.11 and deployment selects Python 3.x.
- The local extension is installed with `-e tools/zensical_extensions`. MkDocs and autorefs remain dependencies of `mkdocstrings`; site commands use Zensical.
- Versioned deployment uses the compatible Mike fork at `2d4ad799442f4592db8ad53b179bfb33db8c69ac` and ANTA's deployment/normalization scripts.

[Zensical 0.0.68](https://github.com/zensical/zensical/releases/tag/v0.0.68) includes native audio/video support, closer macros compatibility, and UI 0.0.35 search-result instant navigation and accessibility fixes. It requires Python >=3.11. Features inherited from earlier releases include redirects, snippet-dependent rebuilds, blog/RSS, API generators, social cards, Markdown exports, and asset exclusions. Availability does not imply adoption.

[Zensical 0.0.69](https://github.com/zensical/zensical/releases/tag/v0.0.69) adds `nav-weight` and `markdownextradata` compatibility, improves symlink watching, fixes Unicode minification crashes, and preserves emojis in Markdown exports. UI 0.0.36 includes navigation spacing and instant-navigation fixes. All three pins already use this version on `main`. Markdown exports remain blocked (D05); check browser behavior when changing the relevant UI or upgrading documentation tooling (D03/D04/D10).

## Decision register

This register is the durable record of migration choices, including features deliberately left disabled. **Adopted** means an agreed convention is in effect; **retained** means the current implementation remains the default; **deferred** means no adoption is planned until the revisit condition is met; **blocked** means a demonstrated problem prevents adoption. None of these statuses means a feature is rejected forever.

The entries below record the current choices and when to reconsider them, as of October 22, 2026. Keep numbering consecutive when entries are added or removed. Deferred features stay here until there is a concrete need or relevant upstream improvement; they do not each need a planned PR.

| ID | Decision and status | Reason / evidence | Revisit when |
| --- | --- | --- | --- |
| D01 | **Deferred:** API backlinks remain disabled for now. Keep forward links through autorefs; #1828 converts the remaining authored object links. | PR #1809 preview showed repeated “Referenced by” blocks cluttering long API pages; maintainer feedback favored removing them. | Upstream offers selective/collapsed backlinks, or readers identify a concrete reverse-navigation need. Compare a small preview against the current API pages and obtain maintainer feedback before enabling them. |
| D02 | **Adopted:** preserve published page and heading URLs with native redirects when content moves. | Contributor guidance in PR #1809 protects external links/bookmarks without placeholder redirect maps. Historical builds change only when rebuilt. | A real page/heading move requires a mapping, or versioned preview exposes incorrect fragment handling. Verify direct entry and instant navigation within the selected version. |
| D03 | **Retained:** custom lightbox layout, aspect-preserving fit, and two-times zoom. | The native-only experiment made images too small and lost useful zoom. Native GLightbox and the ANTA fallback cover different images. Slow-drag logic was fixed in PR #1809; full browser coverage is not claimed. | Native behavior demonstrably covers tall SVG/raster fitting, zoom, pan, touch, palettes, and navigation. Reduce CSS/helper code only after a side-by-side browser comparison. |
| D04 | **Retained:** custom Mermaid fullscreen/zoom and asynchronous initialization. | Upstream label-color fixes do not replace these interactions. The reported missing Zoom button after instant navigation required observing the rendered element instead of the temporary source block. | A native replacement covers fullscreen, scale controls, panning, links, keyboard/focus, palettes, and instant navigation, with regression evidence. |
| D05 | **Blocked:** rendered Markdown exports and Copy as Markdown remain disabled. | The 0.0.67 experiments lost API autorefs links and created missing Markdown destinations; cleanup also affected images. Measurements and reproduction details are preserved below. | A runtime retest on the target version preserves object links and complete destinations. Decide image/source-listing policy and verify clipboard contents under real Mike prefixes before adoption. Do not hard-code authored API links to conceal exporter defects. |
| D06 | **Retained:** curated API pages/navigation; #1828 changes object references while preserving overview-page links. | ANTA's test/input pages include pairing, examples, filters, compatibility notes, and custom templates. Wholesale generation could lose content or duplicate objects. | A small coverage audit with one generator finds missing public objects or demonstrably removes boilerplate while preserving URLs, navigation, object targets, and curated content. |
| D07 | **Retained:** standard Python-Markdown admonitions. GitHub alerts (`gh-admonitions`) and Obsidian callouts (`callouts`) remain deferred. | No identified shared-source need justifies another authoring convention. | Actual Markdown needs to render in GitHub or Obsidian as well as the site. Compare both renderers and document the resulting convention. |
| D08 | **Retained:** local Git date extension. | The footer must follow renames and ignore metadata/license-only edits. Its display string is not RSS timestamp metadata. Native support is tracked in [backlog #18](https://github.com/zensical/backlog/issues/18). | Native support can satisfy those date semantics. Check at Zensical upgrades and compare representative pages before replacing the extension. |
| D09 | **Retained:** compatible Mike fork and deployment/normalization helpers. | They preserve version order, stable aliases, same-base prerelease cleanup, and historical final builds. A strict site build does not test deployment behavior. | Native/upstream alternatives satisfy these contracts in a disposable-origin integration test, including identical redeploys. Never use the production publishing wrapper for a preview. |
| D10 | **Adopted:** documentation tooling and library Python support are independent; dependency updates do not enable features automatically. | Zensical 0.0.69 requires Python >=3.11. The root doc group and both hook environments share its pin. | Every documentation-tooling upgrade: align all three pins and check group/interpreter constraints, builds, inventories, and browser behavior without silently changing library support. |
| D11 | **Deferred:** social cards. | Native support is available, but branding, fonts/assets, caching, versioned URLs, and build cost need evaluation. | A small branded preview demonstrates useful shared-link presentation at acceptable cost. |
| D12 | **Deferred:** instant link previews. | They may help long API pages but can add clutter and interfere with overlays. | A representative guide/API pilot improves navigation and works with keyboard, touch, palettes, and overlays. |
| D13 | **Deferred:** build-only asset exclusions. | A temporary narrow pilot worked, but exclusions can filter source documents and effective resources, including theme assets. | An output inventory identifies unnecessary public copies and a narrow comparison proves source reads, raw snippets, downloads, images, templates, and site assets survive. |
| D14 | **Deferred:** blog and RSS. | There is no publication owner or agreed feed date/version policy. | A named owner commits to maintained articles and defines dates, versioned URLs, and duplicate-entry policy. |
| D15 | **Deferred:** table reader. | Moving manually maintained rows into another file alone does not remove drift. | An authoritative structured dataset can generate a reference table with preserved links and a single maintenance source. |
| D16 | **Deferred:** audio/video. | Available support alone does not establish a learning need; media adds accessibility and asset costs. | A concrete explanation benefits from media with accessible text/captions, versioned playback, and acceptable page/build cost. |

### Maintaining the plan

When implementation or investigation changes a choice, update its reason and revisit condition and record the outcome with the PR link below. Keep completed work out of the backlog. Renumber entries when needed; historical follow-up IDs do not need to be preserved.

### Decision history

| Recorded | Decisions | Outcome and evidence |
| --- | --- | --- |
| 2026-10-22 | Current baseline | Refreshed this guide after the October 21 merge of `main` (`97338a6d`) into #1828. Zensical remains at 0.0.69; the recorded decisions are unchanged. Earlier experiment dates and tested versions remain historical evidence. |
| 2026-10-21 | Backlog cleanup ([#1828](https://github.com/aristanetworks/anta/pull/1828)) | Removed completed and duplicate follow-up proposals. The 16 decisions retain their rationale and revisit conditions; no follow-up PRs are scheduled. |
| 2026-10-16 | D10 — Live rebuilds ([#1828](https://github.com/aristanetworks/anta/pull/1828)) | Live trials showed root README and external example edits did not rebuild their dependent pages within 20 seconds. Explicit watch paths for `README.md` and `examples` fix both. Five edit/restore probes passed on Zensical 0.0.69 using served HTML; external changes take about 10 seconds and in-docs changes about 0.5 seconds. No trial content remains. |
| 2026-10-16 | D10 — Zensical 0.0.69 ([#1828](https://github.com/aristanetworks/anta/pull/1828)) | At that time, the branch was based on `upstream/main` at `855d66c1` and aligned the root doc group and both hook pins at 0.0.69. The executable and package metadata confirm 0.0.69 / Python >=3.11. A clean strict build and rendered object-link/inventory audits passed; no backlink blocks were generated. This does not establish browser, touch, export, or deployment acceptance. Markdown exports remain blocked under D05; browser checks belong with changes to the relevant UI or documentation tooling. |
| 2026-10-16 | D01/D06 — API references ([#1828](https://github.com/aristanetworks/anta/pull/1828)) | Replaced 47 authored API object links with autorefs, retaining two overview-page links. A clean strict Zensical 0.0.68 build, rendered page/fragment destination audit, and changed-file/final all-files pre-commit checks passed. Backlinks remain deferred and curated API pages are retained under D01/D06. |
| 2026-10-15 | D01–D16 | Consolidated the choices and earlier experiments from PR #1809 into this register. In particular, backlinks remain deferred because of preview clutter; this is a current choice that can be revisited, not a permanent rejection. |

## Completed work awaiting merge

As of October 22, 2026, both items are implemented and validated in open PR [#1828](https://github.com/aristanetworks/anta/pull/1828), awaiting merge. The detailed evidence remains below.

| Work | Outcome |
| --- | --- |
| API object references | Converted 47 source links, preserved overview-page links, and centralized MD052 labels. All rendered destinations and referenced inventory objects were verified. |
| Live snippet rebuilds | Added explicit watch paths for root `README.md` and `examples`. All five live edit/restore trials passed; every temporary source edit was restored byte-for-byte. |

## Follow-up backlog

No follow-up PRs are currently scheduled. The remaining ideas are covered by the decision register rather than duplicated as proposed PRs:

- Check diagram/lightbox behavior when changing those helpers or investigating a reported problem (D03/D04); do not add a browser suite as a separate project.
- Preserve working redirects, Git dates, and Mike deployment helpers. Recheck upstream/native support during upgrades; qualify replacements only when proposed (D02/D08/D09).
- Check search and accessibility when changing the relevant UI or upgrading documentation tooling; open focused fixes for observed problems (D10).
- Keep Markdown exports blocked until there is demand and evidence addressing the known defects (D05). The 0.0.69 emoji fix does not establish that API links or missing export destinations are fixed.
- Keep curated API pages and leave social cards, previews, and asset exclusions disabled until their recorded revisit conditions are met (D06/D11/D12/D13). The other optional features remain under D07/D14–D16.

Add a numbered follow-up only when there is a concrete problem or an agreed feature to implement. Number any future list consecutively from F01; do not reserve gaps for removed proposals.

## Earlier experiments to preserve

These measurements came from temporary **Zensical 0.0.67** configurations recorded on October 9. They do not qualify the current 0.0.69 baseline, and their trial changes are not enabled in production.

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

- Live rebuilds in [#1828](https://github.com/aristanetworks/anta/pull/1828): ran `zensical serve --dev-addr=127.0.0.1:8128` on 0.0.69 and inserted unique temporary markers into the sources below. Polled served HTML for marker appearance and disappearance after restoring each original file; did not restart or touch including pages between edits. The root README and external Python example failed before the explicit watch paths were added. The final run allowed up to 90 seconds per rebuild, and all five trials passed. Explicit external watch paths trigger broader rebuilds than in-docs snippet dependencies; the first shorter run saw transient HTTP 404 responses during rebuilding. These timings describe this local run, not a performance guarantee.

  | Included source | Dependent page(s) checked | Edit / restore observed |
  | --- | --- | --- |
  | Root `README.md` | Home | 9.94 s / 9.65 s |
  | `docs/snippets/anta_nrfu_help.txt` | NRFU and Getting Started | 0.51 s / 0.51 s |
  | `docs/snippets/getting-started/inventory.yml` | Getting Started | 0.51 s / 0.51 s |
  | `docs/api/class-diagram.mmd` | Class Diagram, both hidden source and Mermaid block | 0.51 s / 0.51 s |
  | `examples/anta_runner.py` | Getting Started | 9.43 s / 9.41 s |

- API references in [#1828](https://github.com/aristanetworks/anta/pull/1828): Zensical 0.0.69 clean strict build passed. All 47 source references (48 rendered occurrences because the snippet appears twice) resolve to existing HTML pages/fragments; all 18 unique object IDs appear in the 891-entry Sphinx v2 inventory. The complete `AntaTest.render` signature remains linked, full model links reach the dedicated API page, and no backlink blocks were generated.

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

- Verify the executable reports 0.0.69. Check rendered guide-to-API destinations, the Git date footer, `objects.inv`, and absence of backlink blocks.
- Run changed-file pre-commit checks first and all-files checks for final validation. Review any hygiene changes before accepting them.
- Record browser results with changes to the diagram/lightbox helpers (D03/D04); a build or event harness alone does not establish browser acceptance.
- For URL/version changes, use a disposable local Mike main/release preview. Check direct entry and instant navigation, including targets inside details or tabs.
- Run deployment wrapper experiments only in a disposable repository with a local bare origin. The real wrapper publishes to `origin/gh-pages`; it is not a local preview command.
