"""Secrets gate: gitleaks over the Git history and over the working tree."""

from __future__ import annotations

import json

from common import GateResult, GateRun, HARNESS_DIR, failure, gate_main, git_root

CONFIG = HARNESS_DIR / "config" / "gitleaks.toml"
MISSING = "install gitleaks: brew install gitleaks"


def scan(gate: GateRun, mode: str) -> list[dict[str, object]]:
    """Run one gitleaks scan (`git` or `dir`) and return a failure per finding."""
    root = git_root()
    report = gate.folder / f"gitleaks-{mode}.json"
    command = [
        "gitleaks", mode, "--config", str(CONFIG), "--no-banner", "--redact",
        "--report-format", "json", "--report-path", str(report), str(root),
    ]
    status, _, err = gate.run(command, cwd=root)
    if status == 127:
        return [failure("gitleaks", "gitleaks is installed", MISSING, [])]
    if not report.exists():
        return [failure("gitleaks", "a report", err[-500:] or f"no report from {mode}", [])]
    found = json.loads(report.read_text() or "[]")
    return [
        failure(f["RuleID"], "no secret", f"{mode} scan: {f['File']}:{f['StartLine']}", [])
        for f in found
    ]


def run(gate: GateRun) -> GateResult:
    """Scan history and working tree; any finding, or a scan that cannot run, fails."""
    failures = scan(gate, "git") + scan(gate, "dir")
    return gate.finish(failures, ok_exits=(0, 1))


if __name__ == "__main__":
    gate_main("secrets", run)
