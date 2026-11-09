"""Fair integers in a range and fractions in [0, 1)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from lcgkit.core.lcg import ParameterSet, warnings_for
from lcgkit.errors import LcgError

MAX_CONSECUTIVE_DISCARDS = 1_000_000


@dataclass(frozen=True)
class BoundedResult:
    """Values drawn, the outputs used (discarded ones included), the next state, warnings."""

    values: list[int] | list[float]
    outputs_consumed: int
    next_state: int
    warnings: list[str]


def integers(p: ParameterSet, seed: int, lo: int, hi: int, count: int) -> BoundedResult:
    """Draw `count` integers from lo..hi, each equally likely: discard-and-retry on the
    high-order part of the output, never a remainder and never rounding.

    Task: T069. Covers: FR-019, FR-020, FR-021, FR-048.
    """
    size = hi - lo + 1
    if size == 1:
        return BoundedResult([lo] * count, 0, seed, warnings_for(p, seed))
    q = p.m // size
    limit = size * q
    values: list[int] = []
    x, consumed, discards = seed, 0, 0
    while len(values) < count:
        x = (p.a * x + p.c) % p.m
        consumed += 1
        if x < limit:
            values.append(lo + x // q)
            discards = 0
            continue
        discards += 1
        if discards > MAX_CONSECUTIVE_DISCARDS:
            raise LcgError(
                "unsupported-combination",
                "this generator keeps producing values that must be discarded from this seed",
                "seed",
            )
    return BoundedResult(values, consumed, x, warnings_for(p, seed))


def fractions(p: ParameterSet, seed: int, count: int) -> BoundedResult:
    """Draw `count` fractions output / m, kept strictly below 1.0.

    Task: T069. Covers: FR-022.
    """
    below_one = math.nextafter(1.0, 0.0)
    values: list[float] = []
    x = seed
    for _ in range(count):
        x = (p.a * x + p.c) % p.m
        values.append(min(x / p.m, below_one))
    return BoundedResult(values, count, x, warnings_for(p, seed))
