"""The single harness entry point.

Usage: uv run python .harness/run_harness.py [--gates a,b] [--run-id ID]
Runs the gates in a fixed order, each as its own subprocess, writes the results to
evidence/harness-results/<run-id>/ and prints one line per gate and a final PASS or FAIL.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from common import (
    DEFAULT_TIMEOUT,
    HARNESS_DIR,
    STATUS_FAIL,
    STATUS_PASS,
    GateResult,
    failure,
    last_lines,
    new_run_folder,
    repo_root,
)
from feedback import write_feedback

GATES = (
    "lint", "length", "types", "security", "secrets", "audit",
    "tests", "mutation", "contract", "integrity", "traceability",
)
GATE_TIMEOUT = {"mutation": 3600, "tests": 1800, "contract": 1800}


def run_gate(name: str, folder: Path) -> GateResult:
    """Run one gate script in a subprocess and read its result; a crash counts as FAIL."""
    env = {**os.environ, "PYTHONPATH": str(HARNESS_DIR)}
    command = [sys.executable, "-m", f"gates.{name}", "--folder", str(folder)]
    started = time.perf_counter()
    try:
        done = subprocess.run(
            command, cwd=repo_root(), env=env, capture_output=True, text=True,
            timeout=GATE_TIMEOUT.get(name, DEFAULT_TIMEOUT),
        )
        crash = done.stderr if done.returncode != 0 else ""
    except subprocess.TimeoutExpired:
        crash = "the gate did not finish in time"
    result_file = folder / f"{name}.result.json"
    if not crash and result_file.exists():
        return GateResult(**json.loads(result_file.read_text()))
    elapsed = round(time.perf_counter() - started, 2)
    observed = last_lines(crash or "the gate wrote no result", 20)
    return GateResult(
        name, STATUS_FAIL, " ".join(command), 1, elapsed, "", "",
        [failure("gate-crashed", "the gate finishes and reports", observed, [])],
    )


def main() -> int:
    """Run the selected gates; return 0 only if every one passed."""
    parser = argparse.ArgumentParser(description="Run the lcgkit quality gates.")
    parser.add_argument("--gates", default=",".join(GATES), help="comma-separated gate names")
    parser.add_argument("--run-id", default=time.strftime("%Y%m%d-%H%M%S"))
    args = parser.parse_args()
    chosen = [g for g in GATES if g in args.gates.split(",")]
    unknown = set(args.gates.split(",")) - set(GATES)
    if unknown or not chosen:
        print(f"unknown gates: {sorted(unknown)}; choose from {', '.join(GATES)}")
        return 2
    folder = new_run_folder(args.run_id)
    results = []
    for name in chosen:
        result = run_gate(name, folder)
        results.append(result)
        print(f"{result.status}  {name:<13} {result.duration_seconds:>8.2f} s")
    (folder / "results.json").write_text(json.dumps([asdict(r) for r in results], indent=2))
    write_feedback(results, folder)
    passed = all(r.status == STATUS_PASS for r in results)
    verdict = STATUS_PASS if passed else STATUS_FAIL
    (folder / "summary.txt").write_text(
        "\n".join(f"{r.status} {r.name}" for r in results) + f"\n{verdict}\n"
    )
    if len(chosen) < len(GATES):
        print(f"(partial run: {', '.join(chosen)})")
    print(f"results: {folder}")
    print(verdict)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
