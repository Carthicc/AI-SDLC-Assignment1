"""The recurrence x -> (a*x + c) mod m, and sequences of its values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterSet:
    """The multiplier, increment and modulus of a generator."""

    a: int
    c: int
    m: int


@dataclass(frozen=True)
class SequenceResult:
    """Outputs of a run, how many generator outputs it used, the next state and warnings."""

    outputs: list[int]
    outputs_consumed: int
    next_state: int
    warnings: list[str]


def step(p: ParameterSet, x: int) -> int:
    """Return the state after one step from `x`.

    Task: T060. Covers: FR-002.
    """
    return (p.a * x + p.c) % p.m


def warnings_for(p: ParameterSet, seed: int) -> list[str]:
    """Return the warnings that apply to a generator started at `seed`.

    Task: T060. Covers: FR-007.
    """
    found = []
    if p.c == 0 and seed == 0:
        found.append("zero-fixed-point")
    if p.a in (0, 1):
        found.append("degenerate-multiplier")
    return found


def sequence(p: ParameterSet, seed: int, count: int) -> SequenceResult:
    """Return the next `count` outputs after `seed` (the seed itself is not included).

    Task: T060. Covers: FR-002, FR-003, FR-004.
    """
    a, c, m = p.a, p.c, p.m
    outputs: list[int] = []
    append = outputs.append
    x = seed
    for _ in range(count):
        x = (a * x + c) % m
        append(x)
    return SequenceResult(outputs, count, x, warnings_for(p, seed))
