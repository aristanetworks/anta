<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Zensical documentation status

**Baseline:** Zensical `0.0.71`; based on `upstream/main` at `3cfdfe74`. **Updated:** October 29, 2026.

Keep this as a short current-state tracker: what is in place, what was deliberately left out, and outstanding work. Versions refer to ANTA's implementation or verification, not the upstream feature's introduction. Preserve the reason, the condition for reconsidering it, and a PR or compact finding where needed to understand a decision later; a chronological experiment log is unnecessary.

## In place

| What | Since / verified with | Decision rationale |
| --- | --- | --- |
| Zensical site, search, navigation, code copying, and mkdocstrings API pages | 0.0.46 — [#1522](https://github.com/aristanetworks/anta/pull/1522) | Migration is complete; retain the working documentation features. |
| Compatible Mike fork and deployment helpers | 0.0.46 — #1522 | Preserve version order, stable aliases, prerelease cleanup, and historical final builds. Keep until an upstream replacement covers these requirements. |
| Native TOML configuration | 0.0.62 — [#1752](https://github.com/aristanetworks/anta/pull/1752) | Use the supported Zensical configuration format. |
| Local Git date extension | Present by 0.0.62 — #1752 | Follow renames and ignore metadata/license-only changes. Native replacement is tracked in [upstream backlog #18](https://github.com/zensical/backlog/issues/18). |
| Custom lightbox fit/zoom and Mermaid fullscreen/zoom | Retained and fixed with 0.0.68 — [#1809](https://github.com/aristanetworks/anta/pull/1809) | Native behavior did not cover the required interactions. Fixed slow-drag handling and delayed diagram initialization after navigation. |
| Redirect convention for moved pages/headings | 0.0.68 — #1809 | Preserve published links when content moves; add mappings when a real move occurs. |
| Python >=3.11 for documentation tooling, independent of library support | 0.0.68 — #1809 | Match Zensical's requirement without changing ANTA's supported Python versions. Keep the doc group and both hook pins aligned. |
| Authored API object links through autorefs, with centralized MD052 labels | Shipped with 0.0.69 — [#1828](https://github.com/aristanetworks/anta/pull/1828); first validated on 0.0.68 | Resolve object destinations from the API inventory; retain ordinary overview-page links. |
| Live rebuilds for included snippets and Mermaid | 0.0.69 — #1828 | Explicit README/examples watch paths fix external-source rebuilds. All five edit/restore probes passed. |
| Markdown export investigation completed | Retested on 0.0.70 | The Python-library guide has 37 object links in HTML and none in any exported variant. Selected exports miss 6 Markdown destinations; exporting all pages fixes those files. Image removal is an accepted, intentional text-export cleanup behavior. |
| Keep custom API implementation listings marked as source content | Shipped in [#1853](https://github.com/aristanetworks/anta/pull/1853) on 0.0.71; export behavior verified on 0.0.70 | Retain the standard `mkdocstrings-source` class on both custom source wrappers. Export validation reduced BGP implementation listings from 33 to 0 while keeping all 24 examples/expected-results sections and unchanged HTML source content. This marker is retained independently of the decision to leave exports disabled. |
| Exclude build-only scripts from published output | 0.0.70 — [#1840](https://github.com/aristanetworks/anta/pull/1840), merged | Exclude only `scripts/**`; the output comparison retained all intended documentation and browser assets. |
| Curated test/input-model API coverage and type links | BGP shipped in [#1853](https://github.com/aristanetworks/anta/pull/1853); remaining modules implemented here on 0.0.71 | Expanded the BGP audit across all 32 curated test modules. Module-qualified annotations restore 21 links in total shadowed by compatibility attributes; add the missing OSPF input-model section and descriptions for three omitted input fields. Preserve runtime schemas, compatibility aliases, and curated pages. |

## Deliberately not adopted

These are decisions, not an implementation backlog. Revisit only for a concrete need or a relevant upstream improvement.

| What | Current decision and short rationale |
| --- | --- |
| API backlinks | Disabled: repeated “Referenced by” blocks clutter long API pages. Revisit selective/collapsed backlinks if readers need reverse navigation. |
| Markdown exports / Copy as Markdown | Parked, tested on 0.0.70. Purpose: provide rendered text, generated API content, and expanded snippets for AI ingestion or copying into a chat. Its practical benefit for ANTA is unproven: no concrete workflow needs it. API object links disappear; selected exports have missing destinations unless all pages are exported. Image removal is intentional and accepted. No further work is planned unless a concrete need emerges and relevant upstream improvements warrant another look. |
| Wholesale API page generation | Keep curated pages: pairing, examples, filters, compatibility notes, and stable URLs matter more than removing boilerplate. |
| GitHub alerts / Obsidian callouts | Keep standard admonitions: no shared-source requirement warrants another syntax. |
| Replacing custom zoom, Git dates, or Mike helpers | Keep working implementations until native alternatives meet the same requirements. |
| Social cards | Deferred: no agreed branding/use case to justify the assets and build cost. |
| Instant link previews | Deferred: no demonstrated navigation benefit to justify possible clutter and overlay conflicts. |
| Blog / RSS | Deferred: no publication owner or feed date/version policy. |
| Table reader | Deferred: useful with an authoritative dataset; moving manually maintained rows alone does not prevent drift. |
| Audio / video | Deferred: no identified explanation needing media and its accessibility/asset costs. |

## Left to do

After this PR merges, no further implementation is scheduled. The remaining work is conditional maintenance.

| Action | Status / scope |
| --- | --- |
| Revisit upstream replacements during tooling upgrades | Conditional: Git date support, Mike compatibility, and zoom interactions. No replacement PR is needed now. |

For routine upgrades, align all three Zensical pins and run a clean strict build. Check inventory coverage and type links when adding tests or input models. Check browser interactions when the UI or helpers change; use a disposable Mike preview when version URLs or deployment behavior change. Existing maintainer browser testing and DOM regression checks do not establish exhaustive browser/touch coverage. Never use the production publishing wrapper for a local preview.
