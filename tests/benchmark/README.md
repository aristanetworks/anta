<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# ANTA benchmarks

The [CodSpeed workflow](../../.github/workflows/codspeed.yml) runs two separate jobs:

- Simulation on Python 3.12 covers the entire benchmark suite.
- Memory on CPython 3.14.9 covers dry and full ANTA runs with 1, 2, and 5 devices (`test_anta.py`). Each invocation uses a fresh inventory, catalog, and result manager.

## Why memory uses CPython 3.14

On older CPython versions, the native asyncio task registry uses a shared weak set. Removing completed tasks leaves the underlying hash table allocated, with deleted entries. Later task creation can trigger a table resize or compaction depending on the registry's history. A measured invocation can therefore include a large interpreter allocation even when ANTA's workload has not changed. A fixed hash seed does not eliminate this effect.

CPython 3.14 tracks native asyncio tasks using [linked lists with nodes embedded in the tasks](https://github.com/python/cpython/blob/v3.14.9/Modules/_asynciomodule.c#L2203-L2214), removing that shared hash-table resize path. This does not remove all sources of memory variation. The [weak-set fallback for other task implementations](https://github.com/python/cpython/blob/v3.14.9/Modules/_asynciomodule.c#L3724-L3737) still exists; the results below do not qualify PyPy or custom task factories.

The investigation in [PR #1829](https://github.com/aristanetworks/anta/pull/1829) compared 40 fresh native processes: 10 isolated runs and 10 suite runs on each of CPython 3.12.15 and 3.14.9. The [qualification run](https://github.com/aristanetworks/anta/actions/runs/40477854645) used the same ARM runner image, CodSpeed runner 5.5.0, and memtrack 1.6.1. All processes had the same workload fingerprint, and none reset the task registry.

Full-run allocation measurements in the suite runs were:

| Devices | CPython 3.12 peak range (bytes) | CPython 3.12 spread (bytes) | CPython 3.14 peak range (bytes) | CPython 3.14 spread (bytes) |
| --- | --- | --- | --- | --- |
| 1 | 472,282–603,376 | 131,094 | 472,282–472,304 | 22 |
| 2 | 902,742–1,165,857 | 263,115 | 914,975–916,308 | 1,333 |
| 5 | 2,187,912–2,189,464 | 1,552 | 2,187,857–2,189,190 | 1,333 |

Spread is the maximum minus minimum across 10 processes, not total memory usage. These diagnostic peaks track requested bytes from allocations originating inside the measured sample; they are not process RSS, net retained memory, or an exact reproduction of the server-side CodSpeed metric. Dry-run spreads were zero on both runtimes. A matching [ordinary memory job](https://github.com/aristanetworks/anta/actions/runs/40477854768/job/122100901244) passed all six cases and uploaded its measurements.

This evidence supports CPython 3.14 as the routine memory regression signal. It does not establish a universal noise threshold or guarantee that future runs cannot vary. The workflow pins the qualified Python patch and CodSpeed runner version explicitly. Runtime or instrumentation upgrades require checking repeatability again and establishing a comparable baseline.

## Coverage decisions

Keep the six end-to-end memory cases for this change. They retain coverage of the real runner lifecycle, including task creation and result collection, without changing ANTA scheduling or resetting private interpreter state.

Reporter memory benchmarks are worth restoring in a separate change: serialization and report construction can regress independently of the runner, and simulation coverage cannot detect their memory regressions. Before enabling them in the memory job, qualify repeated native runs with populated results for every case and define whether each case measures a fresh or warmed result manager. The existing reporter fixtures copy results once per test, so repeated benchmark invocations share that copy.

Keep runner microbenchmarks in simulation for now. Some include index clearing, result resetting, or coroutine closing inside the measured callback, and some reuse a runner context. Review their measurement boundaries before treating them as memory regression gates. Two also exercise APIs scheduled for removal in ANTA 2.0.

## Interpreting future regressions

- After merging the runtime change, obtain a successful memory run on `main` before interpreting subsequent PR comparisons. A Python 3.12-to-3.14 comparison includes interpreter changes and cannot isolate an ANTA regression.
- Compare base and head with the same runtime, instrumentation, and workload. The catalog is discovered from unit-test fixtures, so adding fixtures can intentionally change the workload.
- Keep correctness testing across all supported Python versions. Choosing 3.14 for routine memory CI does not make it the only optimization target; investigate significant performance changes on representative supported and deployed versions too.
- Use separate RSS or retained-memory investigations when those are the question. This allocation benchmark alone does not establish whole-process memory use or the absence of leaks.
