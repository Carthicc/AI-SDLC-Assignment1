"""Tests for lcgkit.core.validator.validate: the three Hull-Dobell conditions (US3)."""

import pytest
from lcgkit.core.lcg import ParameterSet
from lcgkit.core.validator import validate

from lcgkit.core import presets

pytestmark = [pytest.mark.fr("FR-013"), pytest.mark.fr("FR-014")]

INCREMENT = "increment-not-coprime"
PRIME_FACTOR = "multiplier-minus-one-not-divisible-by-prime-factor"
FOUR = "multiplier-minus-one-not-divisible-by-four"


@pytest.mark.ac("AC-023")
def test_glibc_multiplier_with_an_even_increment() -> None:
    verdict = validate(ParameterSet(a=1103515245, c=24680, m=2**31))
    assert verdict.verdict == "not-full-period"
    assert list(verdict.reasons) == [INCREMENT]
    assert verdict.expected_period is None


@pytest.mark.ac("AC-024")
@pytest.mark.parametrize("name", ["glibc-type0", "numrec", "musl", "pcg-lcg64"])
def test_full_period_presets(name: str) -> None:
    p = presets.get(name)
    verdict = validate(p)
    assert verdict.verdict == "full-period"
    assert verdict.expected_period == p.m
    assert list(verdict.reasons) == []


@pytest.mark.ac("AC-025")
def test_minstd_reasons_come_in_the_fixed_order() -> None:
    verdict = validate(presets.get("minstd"))
    assert verdict.verdict == "not-full-period"
    assert list(verdict.reasons) == [INCREMENT, PRIME_FACTOR]


@pytest.mark.ac("AC-026")
def test_only_the_multiple_of_four_condition_fails() -> None:
    verdict = validate(ParameterSet(a=3, c=1, m=16))
    assert list(verdict.reasons) == [FOUR]


@pytest.mark.ac("AC-026")
def test_smallest_modulus_has_a_full_period() -> None:
    assert validate(ParameterSet(a=1, c=1, m=2)).verdict == "full-period"


@pytest.mark.ac("AC-028")
@pytest.mark.parametrize(
    "p",
    [ParameterSet(5, 3, 16), ParameterSet(16807, 0, 2**31 - 1), ParameterSet(3, 1, 16)],
)
def test_each_condition_is_listed_with_its_result(p: ParameterSet) -> None:
    verdict = validate(p)
    assert [c.name for c in verdict.conditions] == [INCREMENT, PRIME_FACTOR, FOUR]
    failed = [c.name for c in verdict.conditions if not c.passed]
    assert failed == list(verdict.reasons)
