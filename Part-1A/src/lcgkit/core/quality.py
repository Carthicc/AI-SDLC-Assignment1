"""A short, fixed set of measurements on a generator's output, with a cautious verdict."""

from __future__ import annotations

import math
from dataclasses import dataclass

from lcgkit.core.lcg import ParameterSet, sequence
from lcgkit.core.stats import chi_square_p, serial_correlation

NOTICE = "Passing these checks does not show that a generator is random or secure."
FLAG = "low-bits-short-period"
NOT_COMPUTED = "not-computed"
NOT_APPLICABLE = "not-applicable"
UNDEFINED = "undefined"
PASS, FAIL = "pass", "fail"
MAX_PERIOD_MODULUS = 2**24
LOW_BITS = (1, 2, 3)
P_THRESHOLD = 0.01
Z_LIMIT = 2.576
MIN_EXPECTED_PER_BIN = 10
MIN_INDEPENDENCE_SAMPLE = 100


@dataclass(frozen=True)
class Check:
    """One check: its name, the value it looked at and its outcome."""

    name: str
    value: object
    outcome: str


@dataclass(frozen=True)
class QualityReport:
    """The measurements, the checks and the verdict."""

    measured_period: int | str
    chi_square: float
    p_value: float
    serial_correlation: float | str
    low_bit_periods: dict[int, int] | str
    checks: list[Check]
    verdict: str
    notice: str


def cycle_length(a: int, c: int, m: int, seed: int) -> int:
    """Length of the cycle the seed ends up in (Brent's cycle detection)."""
    power = length = 1
    tortoise = seed
    hare = (a * seed + c) % m
    while tortoise != hare:
        if power == length:
            tortoise = hare
            power *= 2
            length = 0
        hare = (a * hare + c) % m
        length += 1
    return length


def _low_bit_periods(p: ParameterSet, seed: int) -> dict[int, int]:
    """Cycle length of the generator reduced modulo 2**bits, for the lowest 1, 2 and 3 bits."""
    periods = {}
    for bits in LOW_BITS:
        modulus = min(2**bits, p.m)
        periods[bits] = cycle_length(p.a % modulus, p.c % modulus, modulus, seed % modulus)
    return periods


def _chi_square(values: list[int], m: int, bins: int) -> float:
    counts = [0] * bins
    for value in values:
        counts[value * bins // m] += 1
    expected = len(values) / bins
    return sum((seen - expected) ** 2 / expected for seen in counts)


def _is_power_of_two(m: int) -> bool:
    return m & (m - 1) == 0


def _period_check(period: int | str, size: int) -> Check:
    if isinstance(period, str):
        return Check("period-covers-sample", period, NOT_APPLICABLE)
    return Check("period-covers-sample", period, PASS if period >= size else FAIL)


def _uniformity_check(p_value: float, size: int, bins: int) -> Check:
    if size / bins < MIN_EXPECTED_PER_BIN:
        return Check("uniformity", p_value, NOT_APPLICABLE)
    return Check("uniformity", p_value, PASS if p_value >= P_THRESHOLD else FAIL)


def _independence_check(correlation: float | str, size: int) -> Check:
    if size < MIN_INDEPENDENCE_SAMPLE or isinstance(correlation, str):
        return Check("independence", correlation, NOT_APPLICABLE)
    limit = Z_LIMIT / math.sqrt(size)
    return Check("independence", correlation, PASS if abs(correlation) <= limit else FAIL)


def _low_bits_check(m: int) -> Check:
    """Informational: flagged whenever m is a power of two, never a failure."""
    if _is_power_of_two(m):
        return Check("low-bits", FLAG, PASS)
    return Check("low-bits", None, NOT_APPLICABLE)


def _verdict(checks: list[Check]) -> str:
    if any(c.outcome == FAIL for c in checks):
        return "defect-detected"
    if any(c.name == "low-bits" and c.value == FLAG for c in checks):
        return "caution"
    return "no-defect-detected"


def report(p: ParameterSet, seed: int, sample_size: int, bins: int) -> QualityReport:
    """Measure the first `sample_size` outputs and judge them.

    Task: T074. Covers: FR-026, FR-029, FR-031.
    """
    values = sequence(p, seed, sample_size).outputs
    period: int | str = NOT_COMPUTED
    if p.m <= MAX_PERIOD_MODULUS:
        period = cycle_length(p.a, p.c, p.m, seed)
    chi = _chi_square(values, p.m, bins)
    p_value = chi_square_p(chi, bins - 1)
    raw = serial_correlation(values)
    correlation: float | str = UNDEFINED if raw is None else raw
    checks = [
        _period_check(period, sample_size),
        _uniformity_check(p_value, sample_size, bins),
        _independence_check(correlation, sample_size),
        _low_bits_check(p.m),
    ]
    low_bits = _low_bit_periods(p, seed) if _is_power_of_two(p.m) else NOT_APPLICABLE
    verdict = _verdict(checks)
    return QualityReport(period, chi, p_value, correlation, low_bits, checks, verdict, NOTICE)
