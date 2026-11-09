"""Types gate: mypy --strict over src; any error fails."""

from __future__ import annotations

import re

from common import GateResult, GateRun, failure, gate_main, tool

ERROR_LINE = re.compile(r"^(?P<where>[^:\n]+:\d+)(?::\d+)?: error: (?P<message>.*)$", re.M)


def run(gate: GateRun) -> GateResult:
    """Run `mypy --strict src` and record each error with its file and line."""
    _, out, _ = gate.run([tool("mypy"), "--strict", "src"])
    failures = [
        failure("mypy", "no type error", f"{m['message']} ({m['where']})", [])
        for m in ERROR_LINE.finditer(out)
    ]
    return gate.finish(failures)


if __name__ == "__main__":
    gate_main("types", run)
