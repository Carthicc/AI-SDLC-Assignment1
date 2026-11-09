"""Traceability gate: every AC and FR in the spec has a test, and no marker names an unknown ID."""

from __future__ import annotations

import ast
import re

from common import GateResult, GateRun, failure, gate_main, marker_ids, python_files, repo_root

SPEC = "specs/001-lcgkit-toolkit/spec.md"
AC_ROW = re.compile(r"^\| (AC-\d{3}) \|", re.M)
FR_ITEM = re.compile(r"^- \*\*(FR-\d{3})\*\*", re.M)


def run(gate: GateRun) -> GateResult:
    """Compare the IDs in the spec with the ac(...) and fr(...) markers under tests/."""
    spec = (repo_root() / SPEC).read_text()
    wanted = set(AC_ROW.findall(spec)) | set(FR_ITEM.findall(spec))
    used = {
        i for path in python_files(repo_root() / "tests") for i in marker_ids(ast.parse(path.read_text()))
    }
    gate.note(f"spec IDs: {len(wanted)}; IDs used by tests: {len(used)}")
    failures = [
        failure("untested-id", "at least one test marker", f"{i} has no test", [i])
        for i in sorted(wanted - used)
    ] + [
        failure("unknown-id", "an ID that exists in the spec", f"marker names {i}", [])
        for i in sorted(used - wanted)
    ]
    return gate.finish(failures)


if __name__ == "__main__":
    gate_main("traceability", run)
