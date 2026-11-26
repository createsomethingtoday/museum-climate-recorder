# Museum climate recorder

A museum technician exports numbered humidity samples. Missing records can make an overnight excursion disappear from a report. The first component checks the sequence numbers in a single recording session. Later labs add an instrument, a clock and a reproducible Linux image.

## Run the worked example

From this directory, with a C++17 compiler and Python 3 installed, run

```sh
c++ -std=c++17 -Wall -Wextra -Werror -pedantic recorder.cpp -o /tmp/museum-recorder
python3 verify.py /tmp/museum-recorder
printf '7\n10\n10\n' | /tmp/museum-recorder
```

The last command should print `accepted 7`, `missing 2`, `accepted 10`, and `stale` on separate lines. A gap tells the technician which sequence positions are absent from this stream. Several causes are possible, including loss during export.

| ID | Requirement for one session |
| --- | --- |
| REC-1 | Accept the first valid unsigned 32-bit decimal sequence at any starting value. Print `accepted N` using its decimal value. |
| REC-2 | Accept each higher value. If positions were skipped, print `missing K` before the acceptance line. K is the number of skipped positions. |
| REC-3 | Print `stale` for duplicates and earlier values. Preserve the most recent accepted sequence. |
| REC-4 | Each input line must contain only ASCII decimal digits and fit the range. Print `invalid` for malformed or out-of-range lines and preserve state. |

The baseline has one producer per process and treats counters as increasing within the session. The seven executable examples in verify.py reference these requirement IDs.

## Your first change request

A technician says, “I need to concatenate two exports, and the second instrument starts counting from zero.” Own the change from requirement to review.

1. Predict what the baseline prints for the lines `42`, `RESET`, `0`. Run it and explain the consequence for the technician.
2. Specify an explicit session boundary. Decide what an exact `RESET` line emits, how consecutive resets behave, and whether a smaller number alone establishes a new session. Explain the trade-off with delayed records.
3. Before editing the implementation, add a black-box test for two sessions and capture the failure. Add cases for a near-match marker and delayed data. Implement the requirement and rerun the suite.
4. Give a reviewer your requirement and executable. Ask them to derive one test independently. Keep their finding, your disposition, the command and the revision reviewed.

You can demonstrate this skill when you can make the change live, explain the state transitions, and identify an assumption a real instrument could violate.

## Build toward the two roles

| Milestone | Systems engineering exercise | Quality and leadership evidence |
| --- | --- | --- |
| 1. Contract and integration | Implement the change request. Split parsing into a C interface and compose it with the C++ recorder. Specify integer ranges and buffer ownership. | Trace each requirement to a unit check and a process-level check. Identify a plausible defect that each layer would miss. |
| 2. Embedded build | Package the recorder in a pinned Buildroot external tree, cross-compile for ARM and boot it in QEMU. Have CI build from a clean checkout and replay a fixture on the guest. | Archive the configuration, toolchain version, image digest and guest transcript. Have another engineer reproduce the run. [Buildroot manual](https://buildroot.org/downloads/manual/manual.html) |
| 3. Timing investigation | On a Linux bench compare periodic sampling under ordinary scheduling and PREEMPT_RT with a POSIX real-time thread. Record wakeup delay separately from sample completion. | Agree on a timing budget before testing. Publish sample count, workload, run duration, percentiles, maximum and misses. Use a timerlat trace to investigate an outlier. Finite runs establish observed behavior under those conditions. [Kernel timerlat documentation](https://docs.kernel.org/tools/rtla/rtla-timerlat.html) |
| 4. Instrument integration | Read a physical temperature or humidity sensor through Linux I²C or UART. Trace one sample from hardware to file. Review the corresponding driver and explain its interrupt or polling model. Extend a test driver on the bench and test removal during acquisition. | Write an interface agreement with a hardware peer. Qualify the bench by disconnecting the sensor and showing the checker catches stale data. Retain the wiring diagram, independent reference reading and recovery log. |
| 5. Clock synchronization | Use two lab hosts with hardware timestamping. Draw the path between the reference, NIC clock, system clock and recorded sample. Collect ptp4l and phc2sys offsets through startup, steady state and reconnection. | Set an offset budget and observation window. Document reference uncertainty and use independent timing instrumentation before claiming physical end-to-end accuracy. [ptp4l manual](https://www.linuxptp.org/documentation/ptp4l/) · [phc2sys manual](https://www.linuxptp.org/documentation/phc2sys/) |
| 6. Release decision | Deliver an offline-installable artifact and rehearse rollback. Deliberately withhold one dependency and observe whether installation fails clearly. | Chair a review with a hardware owner and a software reviewer. Sample requirement coverage, assess one third-party dependency, disposition open defects, and write a one-page ship/hold decision with owners. Track escaped defects and time to verified correction across revisions. |

For a systems interview, walk one missing sample from instrument to trace to fix. For a quality-lead interview, start with a passing suite, show the defect it missed, and explain how you changed the test equipment or release criteria. Record personal contributions, peer contributions and unresolved limitations separately.

After these milestones, branch according to the role. For systems depth, compare ARM and x86 disassembly of the same C function, investigate priority inversion on a bench, or import the recorder into an offline Podman host and verify its resource limits. For quality depth, run an independent requirements-based integration campaign and chair defect triage across two contributors. Record experience with proprietary tools such as LDRA or LynxOS only after hands-on use.

## Bulk export performance

Run `python3 benchmark.py` here to compare the original C++ program against the new `--bulk` mode. Both consume the same 500,000-line synthetic export and write their complete reports to a temporary regular file. The harness checks the output digest after every run. It warms each binary once and alternates order for six measured pairs. Its JSON includes compiler flags, source and fixture hashes, elapsed seconds and median throughput.

Use the default mode for a live pipe where the reader needs each response before sending the next sample. Use `/tmp/museum-recorder --bulk < export.txt > report.txt` for completed exports. Bulk mode reuses a POSIX input buffer and lets the output stream batch writes. Both modes share the sequence checks and integer formatting. Input memory scales with the longest line. Throughput includes cached file I/O and process startup. Sensor latency, sustained disk throughput and crash durability need separate experiments.

To replay the Linux trial from this directory on an ARM64 Docker host:

```sh
docker run --rm --platform linux/arm64 --network none -v "$PWD:/lab:ro" -w /lab gcc:14-bookworm@sha256:5e927c284bf55a7dc796262e311a0703344f62f41f5621eb56843111b1d37e15 python3 benchmark.py
```

The [Cook Code ledger](cook-code/import-throughput/ROUNDS.md) links the measured runs. Compare each optimization with its baseline on the same runtime. The Mac and Linux runs use different compilers, storage paths and operating systems.

## Live acquisition under load

[Replay the Linux experiment](cook-code/live-acquisition/REPLAY.md) to measure how long a live producer waits for each acknowledgment while a second recorder imports a file. Compare idle, shared-CPU and separate-CPU placement. [Measured results and trace interpretation](cook-code/live-acquisition/ROUNDS.md)
