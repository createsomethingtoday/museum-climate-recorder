# Bulk import throughput on the museum recorder

Started 2026-11-26 15:17 UTC. Local portfolio work against the untracked recorder in the primary checkout at 5f9bfab3f. Change only this lab. No release destination beyond the local workspace. Synthetic public data, unchanged trust boundary.

- A1. Preserve the original CLI and all seven contracts including prompt output during a live pipe. Add an explicit file-import mode if buffering changes response timing.
- A2. On the same host and compiler flags, improve median wall-clock records per second for a fixed mixed export versus the original. Run paired alternating trials, verify the entire output and report raw timings. Measure batch throughput only. No universal speed target.
- A3. Keep the baseline and reproduction command available. Independently re-test behavior, failure exit and the comparison. Exercise Linux if an existing local runtime is available. Physical sensor measurements require a separate bench.

Primary metric includes process startup, parsing, formatting and writes to a local regular file. No durable-storage flush requirement. No network or hardware integration in the timed path. Checkpoint after baseline and integrated measurement. Usage unavailable.
