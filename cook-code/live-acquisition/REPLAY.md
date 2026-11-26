# Replay the live pipe experiment

From the sensor-recorder directory on a Mac with ARM64 Docker Desktop, run the following. The guest needs two available virtual CPUs for the final placement comparison. Allow about 256 MiB of temporary storage for the importer input. The harness uses standard Python and regular user access to its own child processes.

```sh
out=$(mktemp -d)
docker run --rm --network none --platform linux/arm64 \
  -v "$PWD:/lab:ro" -v "$out:/out" -w /lab \
  gcc:14-bookworm@sha256:5e927c284bf55a7dc796262e311a0703344f62f41f5621eb56843111b1d37e15 \
  sh -ec 'c++ -std=c++17 -O3 -Wall -Wextra -Werror -pedantic recorder.cpp -o /tmp/recorder &&
          python3 acquisition.py --binary /tmp/recorder --output /out/acquisition.json'
echo "$out/acquisition.json"
```

Each condition warms a new live recorder, sends one synthetic sequence number at a time, and checks the exact acknowledgment. Timing starts before the producer writes and stops after it reads the complete response. This includes the two pipe transfers and time waiting to run. A lab deadline miss is an acknowledgment taking more than one millisecond. The producer waits for each response before sending another, so these results characterize request/response service under a closed-loop workload.

The bulk competitor reads a file of repeated sequence numbers through the real importer, exercising its duplicate-record path, with output discarded. It runs only for the measurement window. Pinning it to the same virtual CPU deliberately creates contention. Moving it to a second virtual CPU tests whether placement matters on this guest.

For any trial, locate the entry in `samples` at the zero-based `summary.maximum_sample_index`. Compare its elapsed time with the recorder and producer runqueue deltas and the padding on both sides of the counter snapshots. These counters measure time a runnable task waited for CPU across the bracket. They aggregate scheduler activity and update at scheduling boundaries. The two tasks' waits can overlap. A larger bracket or deferred accounting weakens attribution. An event-by-event scheduler trace or physical device test would answer different questions.
