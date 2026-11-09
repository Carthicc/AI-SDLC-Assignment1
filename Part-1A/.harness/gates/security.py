"""Security gate: Bandit; a finding of medium severity or above fails."""

from __future__ import annotations

import json

from common import GateResult, GateRun, failure, gate_main, tool

BLOCKING = {"MEDIUM", "HIGH"}


def run(gate: GateRun) -> GateResult:
    """Run `bandit -r src -f json` and record medium and high findings."""
    _, out, _ = gate.run([tool("bandit"), "-r", "src", "-f", "json", "-q"])
    failures = []
    try:
        report = json.loads(out)
    except json.JSONDecodeError:
        return gate.finish([failure("bandit", "a JSON report", out[-500:] or "no output", [])])
    for item in report.get("results", []):
        if item["issue_severity"] in BLOCKING:
            where = f"{item['filename']}:{item['line_number']}"
            failures.append(
                failure(item["test_id"], "no finding of medium severity or above",
                        f"{item['issue_text']} ({where})", [])
            )
    for item in report.get("errors", []):
        failures.append(failure("bandit-error", "every file scanned", str(item), []))
    return gate.finish(failures, ok_exits=(0, 1))


if __name__ == "__main__":
    gate_main("security", run)
