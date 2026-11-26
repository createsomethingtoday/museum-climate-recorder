# Museum recorder live acquisition

## Contract and baseline

Scope is the local portfolio lab in the existing checkout at 5f9bfab3f. Source identity is recorded in the evidence manifest because the lab is untracked. See [brief](BRIEF.md).

On 2026-11-26 the original recorder passed all seven requirements in both interactive and bulk modes inside the pinned ARM64 Linux guest. A direct two-process contention probe showed that the guest actually accumulates runnable wait time in procfs schedstat. This permits observation without privileged tracing, changes to the VM kernel, or continuous system-wide capture. [Baseline log](evidence/r01/baseline.txt)

Added a CPU placement comparison to investigate whether separating the importer from the live reader changes the measured tail under the same synthetic workload. Experimental budget is one millisecond per acknowledgment. These experiments cover producer-to-reader round trips through local pipes. A physical sensor arrival, sampling-period jitter and end-to-end persistence are separate boundaries.

## Observed guest behavior

500 acknowledgments per condition, after 100 warmup exchanges each. Values in microseconds. Misses count durations strictly above 1,000 µs.

| Bulk importer placement | p50 | p99 | Maximum | Misses |
| --- | ---: | ---: | ---: | ---: |
| Idle | 2.333 | 3.041 | 4.667 | 0 |
| Shared CPU | 2.666 | 5.416 | 3,556.792 | 2 |
| Separate CPU | 2.334 | 2.667 | 12.292 | 0 |

On the shared CPU the worst round trip was sequence 323, raw sample index 223. During the bracket around its 3.556792 ms acknowledgment the producer accumulated 3.553249 ms of runnable wait; its counter reads extended 2.167 µs before the request and 1.541 µs after the read. The recorder accumulated 0.209 µs of runnable wait in its bracket. This implicates a delay scheduling the producer to observe the acknowledgment. The counters neither time-stamp the instant the acknowledgment entered the pipe nor identify exactly which task ran during the wait. The bulk input offset advanced 1,064,960 bytes during the shared-CPU trial and 675,840 bytes on the separate-CPU trial.

The p99 alone would have concealed both misses. The absence of misses in the separate-CPU condition is an observation from this run. CPU topology, fixed trial order, host activity and sampling overhead limit generalization.

[Raw samples](evidence/r01/acquisition.json) · [Summary](evidence/r01/summary.json) · [Reproduction](REPLAY.md) · [Artifact hashes](evidence/r01/artifacts.sha256)

## Independent final re-test

Sol 6.1 replayed the pinned ARM64 build, passed all seven cases in each CLI mode, verified artifact hashes, and recomputed the summaries and trace brackets. The replay had 0 / 2 / 0 misses in idle / shared / separate conditions, with maxima of 4.542 µs / 2.942833 ms / 13.333 µs. Malformed, oversized, stalled and early-exit fixtures aborted the run. An importer that exits before procfs inspection can surface a Python FileNotFoundError; the process reports failure. Bulk progress establishes overlap across each trial. Per-request overlap and the identity of a competing scheduled task were not established.

Functional correctness, CLI and guide quality, and local delivery readiness passed. No recorder code or upstream release changed. This run is complete for the approved local milestone.
