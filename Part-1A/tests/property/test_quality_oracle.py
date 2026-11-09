"""The quality report against the independent reference calculation (US7)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from lcgkit.core.lcg import ParameterSet
from lcgkit.core.quality import report

from tests.oracle import reference as ref

pytestmark = [pytest.mark.ac("AC-055"), pytest.mark.fr("FR-027")]

TOLERANCE = 1e-9
LOW_BITS = (1, 2, 3)


@st.composite
def cases(draw: st.DrawFn) -> tuple[int, int, int, int, int, int]:
    """A small generator (so the oracle is fast), a sample size and a bin count."""
    m = draw(st.one_of(st.integers(2, 300), st.sampled_from([2, 4, 8, 16, 32, 64, 128, 256])))
    a = draw(st.integers(0, m - 1))
    c = draw(st.integers(0, m - 1))
    seed = draw(st.integers(0, m - 1))
    sample = draw(st.integers(2, 300))
    bins = draw(st.integers(1, sample))
    return a, c, m, seed, sample, bins


def oracle_low_bits(a: int, c: int, m: int, seed: int) -> dict[int, int]:
    """Low-bit periods: walk into the cycle first, then measure over two full cycles."""
    inside = ref.step_sequence(a, c, m, seed, m)[-1]
    values = ref.step_sequence(a, c, m, inside, 2 * m)
    return {bits: ref.low_bit_period(values, bits) for bits in LOW_BITS}


@given(cases())
def test_report_matches_the_reference(case: tuple[int, int, int, int, int, int]) -> None:
    a, c, m, seed, sample, bins = case
    p = ParameterSet(a, c, m)
    result = report(p, seed, sample, bins)
    assert result == report(p, seed, sample, bins)
    values = ref.step_sequence(a, c, m, seed, sample)
    assert result.measured_period == ref.brute_period(a, c, m, seed)
    assert result.chi_square == pytest.approx(ref.chi_square(values, m, bins), rel=TOLERANCE)
    correlation = ref.lag1_autocorrelation(values, m)
    if correlation is None:
        assert result.serial_correlation == "undefined"
    else:
        assert result.serial_correlation == pytest.approx(correlation, rel=TOLERANCE, abs=1e-12)
    if m & (m - 1) == 0:
        assert result.low_bit_periods == oracle_low_bits(a, c, m, seed)
    else:
        assert result.low_bit_periods == "not-applicable"
