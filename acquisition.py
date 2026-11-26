"""Linux-only live pipe acquisition; python3 acquisition.py --binary ./recorder.

Writes raw samples and their summary to --output; prints the summary to stdout.
The competing --bulk import is deliberately terminated after the loaded trial.
"""
import argparse
import json
import math
import os
from pathlib import Path
import platform
import select
import subprocess
import tempfile
import time

BUDGET_NS = 1_000_000


class Schedstat:
    def __init__(self, pid):
        self.fd = os.open(f"/proc/{pid}/schedstat", os.O_RDONLY)

    def read(self):
        before = time.monotonic_ns()
        values = list(map(int, os.pread(self.fd, 256, 0).split()))
        after = time.monotonic_ns()
        if len(values) != 3:
            raise RuntimeError("Malformed Linux schedstat")
        return {"read_start_ns": before, "read_end_ns": after,
                "runtime_ns": values[0], "runqueue_ns": values[1],
                "timeslices": values[2]}

    def close(self):
        os.close(self.fd)


def input_position(pid):
    for line in Path(f"/proc/{pid}/fdinfo/0").read_text().splitlines():
        if line.startswith("pos:"):
            return int(line.split()[1])
    raise RuntimeError("Bulk input position unavailable")


def delta(before, after):
    result = {key: after[key] - before[key]
              for key in ("runtime_ns", "runqueue_ns", "timeslices")}
    if min(result.values()) < 0:
        raise RuntimeError("Nonmonotonic schedstat")
    return result


def exchange(proc, sequence, deadline):
    payload = f"{sequence}\n".encode("ascii")
    start = time.monotonic_ns()
    if os.write(proc.stdin.fileno(), payload) != len(payload):
        raise RuntimeError("Partial request write")
    response = bytearray()
    while not response.endswith(b"\n"):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([proc.stdout], [], [], remaining)[0]:
            raise RuntimeError("Acquisition deadline exceeded")
        chunk = os.read(proc.stdout.fileno(), 64)
        if not chunk:
            raise RuntimeError("Recorder exited before acknowledgment")
        response.extend(chunk)
        if len(response) > 64:
            raise RuntimeError("Oversized acknowledgment")
    end = time.monotonic_ns()
    if time.monotonic() > deadline:
        raise RuntimeError("Acquisition deadline exceeded after read")
    if response != b"accepted " + payload:
        raise RuntimeError(f"Invalid acknowledgment: {bytes(response)!r}")
    return start, end


def stop(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
    for stream in (proc.stdin, proc.stdout, proc.stderr):
        if stream:
            stream.close()


def trial(args, loaded, fixture, bulk_cpu=None):
    processes, counters = [], []
    try:
        live = subprocess.Popen([args.binary], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                bufsize=0)
        processes.append(live)
        producer_stat, recorder_stat = Schedstat(os.getpid()), Schedstat(live.pid)
        counters.extend([producer_stat, recorder_stat])
        bulk = bulk_stat = None
        deadline = time.monotonic() + args.trial_timeout
        for sequence in range(args.warmup):
            exchange(live, sequence, min(deadline, time.monotonic() + args.sample_timeout))
        if loaded:
            with fixture.open("rb") as incoming:
                bulk = subprocess.Popen([args.binary, "--bulk"], stdin=incoming,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        preexec_fn=(lambda: os.sched_setaffinity(0, {bulk_cpu}))
                                        if bulk_cpu is not None else None)
            processes.append(bulk)
            bulk_stat = Schedstat(bulk.pid)
            counters.append(bulk_stat)
            initial = bulk_stat.read()
            while (bulk_stat.read()["runtime_ns"] <= initial["runtime_ns"] or
                   input_position(bulk.pid) <= 0):
                if bulk.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Bulk import failed to make CPU progress")
        bulk_position_before = input_position(bulk.pid) if bulk else None
        bulk_before = bulk_stat.read() if bulk else None
        samples = []
        for index in range(args.samples):
            if bulk and bulk.poll() is not None:
                raise RuntimeError("Bulk import ended before loaded trial completed")
            before = {"producer": producer_stat.read(), "recorder": recorder_stat.read()}
            start, end = exchange(live, args.warmup + index,
                                  min(deadline, time.monotonic() + args.sample_timeout))
            after = {"producer": producer_stat.read(), "recorder": recorder_stat.read()}
            samples.append({"sequence": args.warmup + index, "start_ns": start,
                            "end_ns": end, "latency_ns": end - start,
                            "schedstat_before": before, "schedstat_after": after,
                            "scheduler_deltas": {role: delta(before[role], after[role])
                                                 for role in before},
                            "scheduler_window_padding_ns": {
                                role: {"before": start - before[role]["read_start_ns"],
                                       "after": after[role]["read_end_ns"] - end}
                                for role in before}})
        bulk_after = bulk_stat.read() if bulk else None
        bulk_position_after = input_position(bulk.pid) if bulk else None
        if bulk and (bulk.poll() is not None or
                     bulk_after["runtime_ns"] <= bulk_before["runtime_ns"] or
                     bulk_position_after <= bulk_position_before):
            raise RuntimeError("Bulk did not remain alive and make CPU progress across trial")
        live.stdin.close()
        if live.wait(timeout=args.sample_timeout) != 0 or live.stdout.read(1):
            raise RuntimeError("Recorder exit or trailing output invalid")
        values = sorted(s["latency_ns"] for s in samples)
        summary = {"count": len(values), "p50_ns": values[math.ceil(.5 * len(values)) - 1],
                   "p99_ns": values[math.ceil(.99 * len(values)) - 1],
                   "max_ns": values[-1], "budget_ns": BUDGET_NS,
                   "misses": sum(v > BUDGET_NS for v in values),
                   "maximum_sample_index": max(range(len(samples)), key=lambda i: samples[i]["latency_ns"])}
        return {"condition": "bulk_separate_cpu" if bulk_cpu is not None else
                ("bulk" if loaded else "idle"), "bulk_cpu": bulk_cpu, "summary": summary,
                "samples": samples, "bulk_before": bulk_before, "bulk_after": bulk_after,
                "bulk_delta": delta(bulk_before, bulk_after) if bulk else None,
                "bulk_input_position_before": bulk_position_before,
                "bulk_input_position_after": bulk_position_after,
                "bulk_completion": "terminated after measurement" if bulk else None}
    finally:
        for counter in counters:
            counter.close()
        for proc in reversed(processes):
            stop(proc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=lambda p: str(Path(p).resolve()))
    parser.add_argument("--output", type=Path, default=Path("acquisition.json"))
    parser.add_argument("--samples", type=int, default=500)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--bulk-mib", type=int, default=256)
    parser.add_argument("--sample-timeout", type=float, default=2)
    parser.add_argument("--trial-timeout", type=float, default=30)
    args = parser.parse_args()
    if (min(args.samples, args.warmup, args.bulk_mib) <= 0 or
            not all(math.isfinite(x) and x > 0 for x in (args.sample_timeout, args.trial_timeout))):
        parser.error("Counts and finite deadlines must be positive")
    original_affinity = os.sched_getaffinity(0)
    cpu = min(original_affinity)
    os.sched_setaffinity(0, {cpu})  # Both children inherit this same CPU.
    try:
        with tempfile.TemporaryDirectory(prefix="recorder-acquisition-") as directory:
            fixture = Path(directory) / "import.txt"
            with fixture.open("wb") as handle:
                for _ in range(args.bulk_mib):
                    handle.write(b"1\n" * (1024 * 512))
            result = {"platform": platform.platform(), "architecture": platform.machine(),
                      "python": platform.python_version(), "config": {
                          **vars(args), "output": str(args.output)},
                      "allowed_cpus_before": sorted(original_affinity), "pinned_cpu": cpu,
                      "clock": "monotonic_ns", "percentiles": "nearest rank",
                      "protocol": "one outstanding request, warm each live process then identical numbered stream",
                      "bulk_workload": {"bytes": fixture.stat().st_size,
                                        "records": args.bulk_mib * 1024 * 512,
                                        "content": "1 newline repeated; first accepted, remaining stale"},
                      "trace_scope": "schedstat descriptors remain open; per-sample deltas bracket the latency window and include the recorded before/after padding. Runqueue time cannot be attributed entirely to request latency. Linux scheduler accounting may update at schedule boundaries. No physical sensor or hard deadline guarantee.",
                      "trials": [trial(args, False, fixture), trial(args, True, fixture)]}
            other_cpus = sorted(original_affinity - {cpu})
            if other_cpus:
                result["trials"].append(trial(args, True, fixture, other_cpus[0]))
            else:
                result["mitigation_skipped"] = "Only one allowed CPU"
            args.output.write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps({t["condition"]: t["summary"] for t in result["trials"]}, indent=2))
    finally:
        os.sched_setaffinity(0, original_affinity)


if __name__ == "__main__":
    main()
