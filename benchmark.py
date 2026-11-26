"""From the lab directory: python3 benchmark.py. Uses POSIX temporary storage."""
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT / "cook-code/import-throughput/baseline.cpp"
COUNT = 500_000


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def benchmark(directory):
    compiler = os.environ.get("CXX", "c++")
    flags = ["-std=c++17", "-O3", "-Wall", "-Wextra", "-Werror", "-pedantic"]
    source = {"baseline": REFERENCE, "bulk": ROOT / "recorder.cpp"}
    commands = {}
    for name, path in source.items():
        binary = directory / name
        subprocess.run([compiler, *flags, path, "-o", binary], check=True)
        commands[name] = [binary] + (["--bulk"] if name == "bulk" else [])
        subprocess.run(["python3", ROOT / "verify.py", *commands[name]], check=True,
                       stdout=subprocess.DEVNULL)
    fixture = directory / "export"
    with fixture.open("wb") as handle:
        for i in range(COUNT):
            if i % 101 == 0:
                handle.write(b"invalid\n")
            else:
                value = i - 1 if i % 97 == 0 else i
                handle.write(f"{value}\n".encode("ascii"))

    trials = {key: [] for key in commands}
    checksums = set()
    output = directory / "report"
    for pair in range(7):  # Warm up both binaries, then alternate first position.
        order = ["baseline", "bulk"] if pair % 2 == 0 else ["bulk", "baseline"]
        for name in order:
            with fixture.open("rb") as incoming, output.open("wb") as outgoing:
                start = time.perf_counter()
                subprocess.run(commands[name], stdin=incoming, stdout=outgoing, check=True)
                seconds = time.perf_counter() - start
            checksums.add(digest(output))
            if pair:
                trials[name].append(seconds)
    if len(checksums) != 1:
        raise RuntimeError("Output mismatch across benchmark runs")
    rates = {name: round(COUNT / statistics.median(values)) for name, values in trials.items()}
    print(json.dumps(dict(platform=platform.platform(), architecture=platform.machine(),
                          compiler=subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
                          flags=flags, source_sha256={k: digest(v) for k, v in source.items()},
                          records=COUNT, fixture_sha256=digest(fixture), output_sha256=checksums.pop(),
                          seconds=trials, median_records_per_second=rates,
                          speedup=round(rates["bulk"] / rates["baseline"], 2)), indent=2))


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as scratch:
        benchmark(Path(scratch))
