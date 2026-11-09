"""Builds feedback.json from the failed gates, for handing to the coding agent unchanged."""

from __future__ import annotations

import json
from pathlib import Path

from common import STATUS_FAIL, GateResult, last_lines


def write_feedback(results: list[GateResult], folder: Path) -> Path | None:
    """Write feedback.json next to results.json; return its path, or None if nothing failed."""
    entries = []
    for result in results:
        if result.status != STATUS_FAIL:
            continue
        out = (folder / result.stdout_path).read_text() if result.stdout_path else ""
        err = (folder / result.stderr_path).read_text() if result.stderr_path else ""
        entries.append(
            {
                "gate": result.name,
                "command": result.command,
                "exit_status": result.exit_status,
                "output_tail": last_lines(out + "\n" + err),
                "failures": result.failures,
                "requirement_and_criterion_ids": sorted(
                    {i for f in result.failures for i in f["ids"]}
                ),
            }
        )
    if not entries:
        return None
    target = folder / "feedback.json"
    target.write_text(json.dumps({"failed_gates": entries}, indent=2))
    return target
