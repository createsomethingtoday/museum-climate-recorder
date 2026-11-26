# Import throughput

Local portfolio artifact. Start 15:17 UTC on 2026-11-26. Automation tier. The original source and seven passing baseline cases are retained in baseline.cpp and evidence/r01/baseline-tests.txt. Restore baseline.cpp as recorder.cpp to roll back the executable.

The baseline emits output before reading the next line. Bulk imports can batch output. Introduced an explicit mode, reused POSIX getline storage, and shared classification and formatting across both modes. The default path preserves its live response timing. The RESET assignment remains open for the learner.

- [macOS ARM64 raw trials](evidence/r01/macos.json)
- [Linux ARM64 Docker Desktop guest raw trials](evidence/r01/linux.json)
- [Reviewed artifact identities](evidence/r01/artifacts.sha256)

Reproduce with the README commands. Each timed pair is on one runtime. Linux uses the container filesystem for temporary files. The Mac and Linux timing intervals overlapped during part of this initial run; treat these as samples on a shared development host. Physical bench, hard deadlines, sustained disk I/O and human portfolio evaluation remain unmeasured.

Independent Sol 6.1 final re-test passed A1–A3. It verified manifest digests, all seven contracts in both modes and the baseline, 10,000 seeded random lines, embedded NUL and high bytes, and long lines up to 131 KB. The default responded between pipe writes. Invalid arguments returned 2 and broken output returned nonzero. On macOS the original and default CLI both treat a directory descriptor as empty input; bulk reports a read error. This inherited default-mode limitation is retained for this throughput comparison.

The independent run measured 334,081 versus 15,526,835 records/s on macOS (46.48×) and 2,339,763 versus 40,984,236 on Linux (17.52×). Both reproduced the full output hash. All three gates passed for local CLI delivery. No physical timing claims. Completed 2026-11-26.
