"""Tests gate: pytest with branch coverage of at least 95%; any failure or shortfall fails."""

from __future__ import annotations

import re

from common import GateResult, GateRun, failure, gate_main, junit_failures, tool

COVERAGE_LINE = re.compile(r"not reached\. Total coverage: ([\d.]+)%")
TOTAL_LINE = re.compile(r"^TOTAL\s.*?(\d+(?:\.\d+)?)%\s*$", re.M)


def run(gate: GateRun) -> GateResult:
    """Run pytest (without tests/contract) and record failing tests and the coverage figure."""
    junit = gate.folder / "junit.xml"
    status, out, _ = gate.run(
        [tool("pytest"), "tests", "--ignore=tests/contract", "--cov=src/lcgkit", "--cov-branch",
         "--cov-report=term-missing", "--cov-fail-under=95", f"--junitxml={junit}", "-q"]
    )
    failures = junit_failures(junit)
    short = COVERAGE_LINE.search(out)
    if short:
        failures.append(
            failure("branch-coverage", "at least 95%", f"{short.group(1)}% total coverage", [])
        )
    total = TOTAL_LINE.search(out)
    gate.note(f"coverage figure: {total.group(1) + '%' if total else 'not reported'}")
    if status == 5:  # pytest exit code for "no tests were collected"
        failures.append(failure("no-tests", "at least one test", "no tests collected", []))
    return gate.finish(failures)


if __name__ == "__main__":
    gate_main("tests", run)
