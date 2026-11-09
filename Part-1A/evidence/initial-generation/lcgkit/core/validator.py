"""Does a parameter set give a full period? The three Hull-Dobell conditions."""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from lcgkit.core.lcg import ParameterSet
from lcgkit.core.numtheory import factor

INCREMENT = "increment-not-coprime"
PRIME_FACTOR = "multiplier-minus-one-not-divisible-by-prime-factor"
FOUR = "multiplier-minus-one-not-divisible-by-four"
FULL = "full-period"
NOT_FULL = "not-full-period"
FOUR_DIVISOR = 4


@dataclass(frozen=True)
class Condition:
    """One of the three conditions and whether the parameters satisfy it."""

    name: str
    passed: bool


@dataclass(frozen=True)
class Verdict:
    """The verdict, the expected period (full period only), the conditions and the failures."""

    verdict: str
    expected_period: int | None
    conditions: list[Condition]
    reasons: list[str]


def validate(p: ParameterSet) -> Verdict:
    """Check the Hull-Dobell conditions for a full period.

    Task: T065. Covers: FR-013, FR-014, FR-015.
    """
    conditions = [
        Condition(INCREMENT, gcd(p.c, p.m) == 1),
        Condition(PRIME_FACTOR, all((p.a - 1) % q == 0 for q in factor(p.m))),
        Condition(FOUR, p.m % FOUR_DIVISOR != 0 or (p.a - 1) % FOUR_DIVISOR == 0),
    ]
    reasons = [c.name for c in conditions if not c.passed]
    if reasons:
        return Verdict(NOT_FULL, None, conditions, reasons)
    return Verdict(FULL, p.m, conditions, reasons)
