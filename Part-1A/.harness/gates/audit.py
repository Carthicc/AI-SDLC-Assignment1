"""Audit gate: pip-audit over the locked dependencies; a vulnerability, or no audit, fails."""

from __future__ import annotations

import json

from common import GateResult, GateRun, failure, gate_main, tool


def run(gate: GateRun) -> GateResult:
    """Export the lock file, audit it, and record each known vulnerability."""
    requirements = gate.folder / "audit-requirements.txt"
    status, _, err = gate.run(
        ["uv", "export", "--frozen", "--all-groups", "--no-hashes", "--no-emit-project",
         "--output-file", str(requirements)]
    )
    if status != 0:
        return gate.finish([failure("uv-export", "the lock file exports", err[-500:], [])])
    _, out, _ = gate.run(
        [tool("pip-audit"), "-r", str(requirements), "--no-deps", "--disable-pip",
         "--format", "json"]
    )
    try:
        report = json.loads(out)
    except json.JSONDecodeError:
        return gate.finish(
            [failure("pip-audit", "an audit report", "the audit could not run", [])]
        )
    failures = []
    for dep in report.get("dependencies", []):
        for vuln in dep.get("vulns", []):
            failures.append(
                failure(vuln["id"], "no known vulnerability",
                        f"{dep['name']} {dep['version']}: {vuln.get('description', '')[:200]}", [])
            )
    return gate.finish(failures, ok_exits=(0, 1))


if __name__ == "__main__":
    gate_main("audit", run)
