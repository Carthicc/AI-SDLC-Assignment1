"""Lint gate: Ruff with the rule sets in pyproject.toml; any finding fails."""

from __future__ import annotations

import json

from common import GateResult, GateRun, failure, gate_main, tool


def run(gate: GateRun) -> GateResult:
    """Run `ruff check src tests` and turn each finding into a failure."""
    _, out, _ = gate.run([tool("ruff"), "check", "src", "tests", "--output-format", "json"])
    failures = []
    try:
        findings = json.loads(out) if out.strip() else []
    except json.JSONDecodeError:
        findings = []
    for item in findings:
        where = f"{item['filename']}:{item['location']['row']}"
        failures.append(failure(item["code"], "no Ruff finding", f"{item['message']} ({where})", []))
    return gate.finish(failures)


if __name__ == "__main__":
    gate_main("lint", run)
