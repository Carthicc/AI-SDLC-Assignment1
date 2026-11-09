"""Mutation gate: mutmut on src/lcgkit/core; a score below 0.85, or a failed run, fails."""

from __future__ import annotations

import re

from common import GateResult, GateRun, failure, gate_main, tool

THRESHOLD = 0.85
MAX_LISTED = 100
RESULT_LINE = re.compile(r"^\s*(?P<name>\S+): (?P<status>[a-z][a-z ]*?)\s*$", re.M)
TESTED = {"killed", "survived", "timeout", "suspicious", "segfault", "no tests"}


def describe(gate: GateRun, name: str) -> str:
    """Return the file and the change made by one mutant, from `mutmut show`."""
    _, out, _ = gate.run([tool("mutmut"), "show", name])
    changes = [line for line in out.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
    files = [line[4:] for line in out.splitlines() if line.startswith("--- ")]
    return f"{files[0] if files else name}: {' | '.join(changes)}"[:400]


def run(gate: GateRun) -> GateResult:
    """Run mutmut, compute killed / tested, and list each surviving mutant."""
    gate.run([tool("mutmut"), "run"], timeout=3600)
    _, out, _ = gate.run([tool("mutmut"), "results", "--all", "true"])
    statuses = {m["name"]: m["status"] for m in (x.groupdict() for x in RESULT_LINE.finditer(out))}
    tested = [n for n, s in statuses.items() if s in TESTED]
    killed = [n for n, s in statuses.items() if s == "killed"]
    gate.note(f"mutants tested: {len(tested)}; killed: {len(killed)}")
    failures: list[dict[str, object]] = []
    if not tested:
        failures.append(failure("mutation", "mutants generated and tested", "none were tested", []))
    elif len(killed) / len(tested) < THRESHOLD:
        score = len(killed) / len(tested)
        failures.append(failure("mutation-score", f"at least {THRESHOLD}",
                                f"{score:.3f} ({len(killed)} of {len(tested)} killed)", []))
        survivors = [n for n in tested if n not in killed][:MAX_LISTED]
        failures += [failure("surviving-mutant", "the mutant is killed", describe(gate, n), [])
                     for n in survivors]
    return gate.finish(failures)


if __name__ == "__main__":
    gate_main("mutation", run)
