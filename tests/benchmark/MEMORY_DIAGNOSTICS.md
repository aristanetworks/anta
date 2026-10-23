<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Native memory repeatability diagnostic

PR [#1822](https://github.com/aristanetworks/anta/pull/1822) exhibited another large memory swing, but its original base/head comparison also crossed native instrument versions. This experiment checks repeatability on one unchanged commit before attributing the swing to an ANTA change.

## Run it

The **Diagnose memory repeatability** workflow runs automatically when a PR changes its workflow or Python helpers, including a draft PR. It checks out the exact PR head SHA. Subsequent ANTA changes do not trigger this workflow unless they touch those diagnostic files.

After merging, use **Actions → Diagnose memory repeatability → Run workflow**, select an unchanged branch or tag, and leave `repetitions` at 10 for the first experiment. All repetitions in a job use the same checkout and installed environment. A separate dispatch can resolve different dependencies or use a newer runner image: compare the environment manifests before combining results.

The job uses `ubuntu-24.04-arm`, Python 3.12.15, native CodSpeed runner 5.4.0 and its pinned memtrack instrument, with physical memory tracking and allocation stacks enabled. The installer checksum comes from the same pinned CodSpeed action as the normal memory workflow. No upload token, OIDC permission, or CodSpeed upload is used.

Each repetition launches four independent native runner/tracker/pytest processes:

- **isolated**: `tests/benchmark/test_anta.py::test_anta[2-devices]` alone.
- **suite**: the normal six cases in `tests/benchmark/test_anta.py`, preserving their collection order.
- **isolated-reset**, **suite-reset**: the same selections with `--anta-reset-task-registry` enabled.

The starting variant rotates each repetition to spread host-level ordering effects across all four variants. Dependencies and native instruments are installed once. Normal bytecode is precompiled and bytecode writes are disabled for all processes, so the first repetition cannot introduce pytest assertion-rewrite caches for later repetitions. Python's hash seed remains zero. The existing cold-inventory setup, teardown, catalog coverage, production scheduling, and native warm-up behavior are retained.

The reset variant clears the existing asyncio task-registration WeakSet in the benchmark's `setup()`, before every warm-up and measured invocation. It does not replace the WeakSet object held by the native asyncio module or change the measured callback. It refuses to run inside an event loop, alongside another Python thread, or while unfinished registered tasks remain. Capability checks support interpreters exposing `_asyncio._scheduled_tasks` or the older `_asyncio._all_tasks` as a WeakSet with an ordinary backing set; there is no hard-coded Python-version gate. Other implementations fail explicitly. The workflow's Python version stays pinned to preserve the experimental comparison.

Metadata records the node ID, exposed registry name, task counts and backing-set size before/after every reset. Native validation requires exactly two resets per selected case (warm-up and measurement), an empty registry after each, and matching post-reset sizes. Baseline variants require no resets. Clearing a quiescent registry is an interpreter-state experiment, not a proposed production change or a claimed stability fix.

## Evidence

Download the run's `memory-repeatability-<run-id>-<attempt>` artifact and extract its tar archive. Artifacts expire after 30 days, so copy useful evidence into the investigation archive.

The separate `memory-summary-<run-id>-<attempt>` artifact contains the small environment manifest, `runs.json` and `summary.md`. It is uploaded before packaging the large raw profiles. It lets you compare all four numerical distributions without downloading the captured stacks.

| File | Purpose |
| --- | --- |
| `environment.json`, `packages.txt`, `install.json` | Commit, runner image, interpreter, installed versions, install provenance, page size, libc, native executable hashes and instrument versions |
| `runs.json`, `summary.md` | Per-process command, exit code, evidence validation, catalog and result-order fingerprints |
| `NN-<variant>/profile/` | Original native allocation/physical-memory events, benchmark timestamps and module/stack artifacts produced by CodSpeed |
| `NN-*/run.log`, `NN-*/junit.xml` | Native execution output, pytest order, ANTA case counts and statuses, test failures |
| `NN-*/metadata/catalog.json` | Actual catalog inputs and mocked responses, exported after measurement |
| `NN-*/metadata/session.json` | Collected pytest order, final measured results/statuses, result-order fingerprint and registry-reset evidence |

The opt-in pytest plugin retains references to existing session fixtures and serializes evidence at session finish, after the suite's final measurement. It does not wrap the runner or add work inside a measured callback. Loading the observer still changes process startup slightly, so this is a diagnostic comparison between identically observed variants, not a replacement baseline for the ordinary job.

`catalog_sha256` normalizes only `VerifyInterfacesCounterDetails.lastStatusChangeTimestamp` values that exactly equal the fixture's import-time `timestamp_one_day_ago`. The raw catalog and `raw_catalog_sha256` retain these changing timestamps; the normalization count is also recorded and checked. No measured input is modified. Other catalog differences fail validation.

Result insertion order currently follows the runner's `gather()` coroutine scheduling order. The result-order fingerprint describes the returned measured full-run invocation, not coroutine completion order or native warm-up invocations. Different fingerprints are evidence to investigate and do not fail this experiment.

The summary checks that the expected one/six cases ran, the two-device result counts and statuses match, native artifacts exist, the reset ran as requested, and the installed environment stayed unchanged. It also independently reconstructs the two-device sample's peak simultaneously-live requested bytes originating from allocation/reallocation calls inside SampleStart/SampleEnd, and its cumulative allocation bytes and large allocation sizes. A realloc of a pre-window pointer contributes its full new size. Marker order and the decoded event count against the native tracker log are validated before accepting the reconstruction.

This allocation-cohort metric is **not** RSS, net process-memory growth, or a replacement CodSpeed dashboard export. The runner's `--skip-upload` mode retains raw profiles without server-side report processing. The numerical arrays do not declare memory stable; compare their distributions and preserve the full profiles for attribution. An independent RSS probe or a macOS fallback run is not equivalent evidence. The pinned msgpack/zstandard analysis dependencies are installed once and are imported only by the parent driver after a native child exits.

## Interpret the experiment

1. Reject failed/incomplete pairs or unexplained environment/catalog differences before comparing memory.
2. Compare the two-device measured interval across isolated repetitions. Persistent high/low bands here would show that preceding benchmark cases are not required for the variability.
3. Compare that interval across suite repetitions, then against isolated runs. A suite-specific difference would justify investigating earlier-case state; isolation alone does not establish its precise mechanism.
4. Compare high/low native allocation stacks and physical-memory events, alongside result-order fingerprints. Keep allocator retention, ordering/lifetime overlap and instrument accounting as hypotheses until the profiles distinguish them.
5. Compare each reset distribution against its matching unchanged variant. Check every reset's before/after metadata. If the familiar bands collapse, that supports registry history as a cause; any registry resize allocations during the measured invocation remain part of its measured cost.

Retain the raw artifacts, exact SHA, environment manifest and extraction/analysis method with any conclusion. This workflow establishes a controlled evidence collection path; it is not a claimed fix for the recurring regression reports.
