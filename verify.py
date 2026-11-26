"""Black-box acceptance tests. Pass the path to the compiled recorder."""
from pathlib import Path
import subprocess
import sys

cases = [
    ("REC-1 first sample", "0\n", "accepted 0\n"),
    ("REC-1 arbitrary start", "87", "accepted 87\n"),
    ("REC-2 contiguous", "7\n8\n", "accepted 7\naccepted 8\n"),
    ("REC-2 gap", "7\n10\n", "accepted 7\nmissing 2\naccepted 10\n"),
    ("REC-3 stale", "9\n9\n2\n10\n", "accepted 9\nstale\nstale\naccepted 10\n"),
    ("REC-4 invalid", "1\n\n-2\n3x\n 4\n4294967296\n2\n",
     "accepted 1\n" + "invalid\n" * 5 + "accepted 2\n"),
    ("REC-2 wide gap", "0\n4294967295\n",
     "accepted 0\nmissing 4294967294\naccepted 4294967295\n"),
]
for name, data, expected in cases:
    run = subprocess.run([Path(sys.argv[1]).resolve(), *sys.argv[2:]], input=data, text=True,
                         capture_output=True, timeout=5, check=True)
    if run.stdout != expected:
        sys.exit(f"{name}: expected {expected!r}, got {run.stdout!r}")
    print("PASS", name)
