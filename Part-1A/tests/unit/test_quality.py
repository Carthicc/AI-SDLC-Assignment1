"""Tests for lcgkit.core.quality.report (US7). Small generators are worked out by hand."""

import pytest
from lcgkit.core.lcg import ParameterSet
from lcgkit.core.quality import QualityReport, report

from lcgkit.core import presets

pytestmark = [pytest.mark.fr("FR-026"), pytest.mark.fr("FR-029"), pytest.mark.fr("FR-031")]

NOTICE = "Passing these checks does not show that a generator is random or secure."
FLAG = "low-bits-short-period"
SMALL = ParameterSet(a=5, c=3, m=16)
CONSTANT = ParameterSet(a=1, c=0, m=16)


def outcomes(result: QualityReport) -> dict[str, str]:
    """Map each check name to its outcome."""
    return {check.name: check.outcome for check in result.checks}


def flagged(result: QualityReport) -> bool:
    """True if the low-bits check carries the short-period flag."""
    return any(c.name == "low-bits" and c.value == FLAG for c in result.checks)


@pytest.mark.ac("AC-049")
def test_a_perfectly_even_full_cycle() -> None:
    result = report(SMALL, 7, 16, 16)
    assert result.measured_period == 16
    assert result.chi_square == 0
    found = outcomes(result)
    assert found["period-covers-sample"] == "pass"
    assert found["uniformity"] == "not-applicable"
    assert found["independence"] == "not-applicable"
    assert flagged(result)
    assert result.verdict == "caution"


@pytest.mark.ac("AC-050")
def test_a_stuck_generator_is_a_defect() -> None:
    result = report(CONSTANT, 3, 16, 16)
    assert result.measured_period == 1
    assert result.chi_square == 240
    assert outcomes(result)["period-covers-sample"] == "fail"
    assert result.verdict == "defect-detected"


@pytest.mark.ac("AC-050")
def test_a_counter_fails_the_uniformity_and_independence_checks() -> None:
    # 1, 2, 3, ... 1000 all land in the first of 10 bins: (1000 - 100)**2 / 100 + 9 * 100 = 9000
    result = report(ParameterSet(a=1, c=1, m=2**20), 0, 1000, 10)
    assert result.chi_square == 9000
    found = outcomes(result)
    assert found["period-covers-sample"] == "pass"
    assert found["uniformity"] == "fail"
    assert found["independence"] == "fail"
    assert result.verdict == "defect-detected"


@pytest.mark.ac("AC-051")
def test_the_serial_correlation_of_a_constant_sequence_is_undefined() -> None:
    assert report(CONSTANT, 3, 16, 16).serial_correlation == "undefined"


@pytest.mark.ac("AC-052")
def test_low_bit_periods_of_the_glibc_generator() -> None:
    result = report(presets.get("glibc-type0"), 1, 1000, 10)
    assert result.low_bit_periods == {1: 2, 2: 4, 3: 8}


@pytest.mark.ac("AC-053")
def test_low_bit_periods_do_not_apply_to_a_modulus_that_is_not_a_power_of_two() -> None:
    result = report(presets.get("minstd"), 1, 1000, 10)
    assert result.low_bit_periods == "not-applicable"
    assert not flagged(result)


@pytest.mark.ac("AC-053")
def test_a_large_modulus_skips_only_the_period() -> None:
    result = report(presets.get("numrec"), 1, 1000, 10)
    assert result.measured_period == "not-computed"
    assert outcomes(result)["period-covers-sample"] == "not-applicable"
    assert isinstance(result.chi_square, float)
    assert isinstance(result.p_value, float)
    assert isinstance(result.serial_correlation, float)
    assert result.low_bit_periods == {1: 2, 2: 4, 3: 8}


@pytest.mark.ac("AC-057")
def test_minstd_passes_every_applicable_check() -> None:
    result = report(presets.get("minstd"), 1, 10_000, 10)
    assert result.chi_square == pytest.approx(6.69, abs=0.005)
    assert result.p_value == pytest.approx(0.6694, abs=0.00005)
    assert result.serial_correlation == pytest.approx(-0.0005, abs=0.00005)
    found = outcomes(result)
    assert found["uniformity"] == "pass"
    assert found["independence"] == "pass"
    assert "fail" not in found.values()
    assert result.verdict == "no-defect-detected"


@pytest.mark.ac("AC-058")
def test_glibc_passes_the_checks_but_raises_the_low_bits_flag() -> None:
    result = report(presets.get("glibc-type0"), 1, 10_000, 10)
    assert result.chi_square == pytest.approx(8.882, abs=0.0005)
    assert result.p_value == pytest.approx(0.4482, abs=0.00005)
    assert result.serial_correlation == pytest.approx(-0.00111, abs=0.000005)
    assert "fail" not in outcomes(result).values()
    assert flagged(result)
    assert result.verdict == "caution"


@pytest.mark.ac("AC-060")
@pytest.mark.parametrize(
    "p", [SMALL, CONSTANT, presets.get("minstd"), presets.get("glibc-type0")]
)
def test_every_report_carries_the_notice(p: ParameterSet) -> None:
    assert report(p, 1, 200, 10).notice == NOTICE
