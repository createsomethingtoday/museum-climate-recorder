# Live acquisition under bulk import

Local museum lab, automation tier. Start 2026-11-26 15:22 UTC. Existing recorder CLI and prior lab artifacts protected. The only production interface exercised is the existing default pipe protocol and --bulk file import. Local educational delivery only. Usage unknown.

L1. Run the same numbered request stream through a warm live process in Linux ARM64 in idle and concurrent bulk conditions. Independently validate every acknowledgment. Use a fixed predeclared 1 ms illustrative budget and report count, p50/p99, maximum and misses; retain raw samples. Model a single outstanding request, measuring just before producer writes through complete acknowledged read.
L2. Verify concurrent bulk activity across the loaded trial and fail closed for early exits, malformed responses or stalled acquisition. Record workload, environment and replay instructions.
L3. Capture a same-trial Linux timing trace and correlate the maximum observed loaded sample, explaining the timing component supported by evidence and residual uncertainty. No physical sensor, hard deadline or general causal guarantee.
L4. Independently re-test CLI, calculations and failure handling. Local-only scope; removing new harness and run notes restores prior lab. Stop once the four criteria have measured evidence.
