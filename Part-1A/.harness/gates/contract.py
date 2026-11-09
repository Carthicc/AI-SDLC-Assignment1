"""Contract gate: Schemathesis tests against the generated OpenAPI description."""

from __future__ import annotations

from common import GateResult, GateRun, failure, gate_main, junit_failures, tool

NO_TESTS = 5  # pytest exit code for "no tests were collected"


def run(gate: GateRun) -> GateResult:
    """Run `pytest tests/contract` and record each failing operation."""
    junit = gate.folder / "contract-junit.xml"
    status, _, _ = gate.run([tool("pytest"), "tests/contract", "-q", f"--junitxml={junit}"])
    failures = junit_failures(junit)
    if status == NO_TESTS:
        failures.append(failure("no-contract-tests", "at least one contract test", "none found", []))
    return gate.finish(failures)


if __name__ == "__main__":
    gate_main("contract", run)
