"""Statistics for the quality report: the chi-square p-value and the serial correlation."""

from __future__ import annotations

import math
from collections.abc import Sequence
from itertools import pairwise

TOLERANCE = 1e-15
MAX_ITERATIONS = 10_000
TINY = 1e-300


def _series(s: float, x: float) -> float:
    """Regularised lower incomplete gamma P(s, x) by its power series (for x < s + 1)."""
    term = 1.0 / s
    total = term
    n = s
    for _ in range(MAX_ITERATIONS):
        n += 1
        term *= x / n
        total += term
        if abs(term) < abs(total) * TOLERANCE:
            break
    return total * math.exp(-x + s * math.log(x) - math.lgamma(s))


def _fraction(s: float, x: float) -> float:
    """Regularised upper incomplete gamma Q(s, x) by a continued fraction (for x >= s + 1)."""
    b = x + 1.0 - s
    c = 1.0 / TINY
    d = 1.0 / b
    h = d
    for i in range(1, MAX_ITERATIONS + 1):
        an = -i * (i - s)
        b += 2.0
        d = an * d + b
        d = TINY if abs(d) < TINY else d
        c = b + an / c
        c = TINY if abs(c) < TINY else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < TOLERANCE:
            break
    return math.exp(-x + s * math.log(x) - math.lgamma(s)) * h


def chi_square_p(statistic: float, dof: int) -> float:
    """Upper-tail probability of the chi-square distribution: Q(dof / 2, statistic / 2).

    Task: T073. Covers: FR-030.
    """
    if statistic <= 0:
        return 1.0
    s = dof / 2.0
    x = statistic / 2.0
    p = 1.0 - _series(s, x) if x < s + 1.0 else _fraction(s, x)
    return min(1.0, max(0.0, p))


def serial_correlation(values: Sequence[int]) -> float | None:
    """Lag-1 serial correlation of the values; None when they are all equal.

    Task: T073. Covers: FR-030.
    """
    if min(values) == max(values):
        return None
    mean = sum(values) / len(values)
    deviations = [v - mean for v in values]
    numerator = sum(left * right for left, right in pairwise(deviations))
    return numerator / sum(d * d for d in deviations)
