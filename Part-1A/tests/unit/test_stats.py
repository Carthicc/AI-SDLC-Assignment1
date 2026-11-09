"""Tests for lcgkit.core.stats: the chi-square p-value and the serial correlation (US7)."""

import pytest
from lcgkit.core.stats import chi_square_p, serial_correlation

from tests.oracle.reference import NIST_CRITICAL_1_PERCENT, lag1_autocorrelation, step_sequence

pytestmark = [pytest.mark.fr("FR-030")]

TOLERANCE = 0.0005


@pytest.mark.ac("AC-059")
@pytest.mark.parametrize(("dof", "critical"), list(NIST_CRITICAL_1_PERCENT.items()))
def test_published_one_percent_critical_values(dof: int, critical: float) -> None:
    assert chi_square_p(critical, dof) == pytest.approx(0.01, abs=TOLERANCE)


@pytest.mark.ac("AC-059")
def test_a_statistic_of_zero_has_p_value_one() -> None:
    assert chi_square_p(0, 5) == 1.0


def test_the_serial_correlation_of_a_constant_sequence_is_undefined() -> None:
    assert serial_correlation([4] * 20) is None


def test_the_serial_correlation_matches_the_reference() -> None:
    values = step_sequence(1103515245, 12345, 2**31, 1, 500)
    expected = lag1_autocorrelation(values, 2**31)
    assert serial_correlation(values) == pytest.approx(expected, rel=1e-9)
