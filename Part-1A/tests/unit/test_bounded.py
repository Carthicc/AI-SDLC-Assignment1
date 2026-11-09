"""Tests for lcgkit.core.bounded: fair integers and fractions (US5)."""

import pytest
from lcgkit.core.bounded import fractions, integers
from lcgkit.core.lcg import ParameterSet

from lcgkit.core import presets

pytestmark = [
    pytest.mark.fr("FR-019"),
    pytest.mark.fr("FR-020"),
    pytest.mark.fr("FR-021"),
    pytest.mark.fr("FR-022"),
]

SMALL = ParameterSet(a=5, c=3, m=16)
FULL_PERIOD = 16


@pytest.mark.ac("AC-035")
def test_one_period_gives_each_value_the_same_number_of_times() -> None:
    result = integers(SMALL, 7, 1, 3, 15)
    values = list(result.values)
    assert [values.count(v) for v in (1, 2, 3)] == [5, 5, 5]
    assert result.outputs_consumed == FULL_PERIOD
    assert result.outputs_consumed - len(values) == 1


@pytest.mark.ac("AC-036")
@pytest.mark.parametrize("size", range(2, FULL_PERIOD + 1))
def test_every_range_size_is_fair_over_one_period(size: int) -> None:
    per_value = FULL_PERIOD // size
    result = integers(SMALL, 7, 0, size - 1, per_value * size)
    values = list(result.values)
    assert [values.count(v) for v in range(size)] == [per_value] * size
    assert result.outputs_consumed <= FULL_PERIOD


@pytest.mark.ac("AC-037")
def test_a_range_with_negative_bounds_stays_inside() -> None:
    values = list(integers(SMALL, 7, -3, 3, 200).values)
    assert len(values) == 200
    assert all(-3 <= v <= 3 for v in values)


@pytest.mark.ac("AC-038")
def test_a_single_value_range_consumes_nothing() -> None:
    result = integers(SMALL, 7, 5, 5, 10)
    assert list(result.values) == [5] * 10
    assert result.outputs_consumed == 0
    assert result.next_state == 7


@pytest.mark.ac("AC-040")
def test_the_weak_low_bit_does_not_decide_the_result() -> None:
    values = list(integers(presets.get("glibc-type0"), 1, 0, 1, 64).values)
    assert set(values) <= {0, 1}
    assert any(values[i] == values[i + 1] for i in range(len(values) - 1))


@pytest.mark.ac("AC-041")
def test_drawing_in_two_parts_equals_drawing_at_once() -> None:
    p = presets.get("glibc-type0")
    whole = integers(p, 1, 1, 6, 10)
    first = integers(p, 1, 1, 6, 4)
    rest = integers(p, first.next_state, 1, 6, 6)
    assert list(first.values) + list(rest.values) == list(whole.values)
    assert rest.next_state == whole.next_state


@pytest.mark.ac("AC-042")
def test_fractions_of_the_worked_example() -> None:
    result = fractions(SMALL, 7, 5)
    assert list(result.values) == [0.375, 0.0625, 0.5, 0.6875, 0.625]


@pytest.mark.ac("AC-043")
def test_a_fraction_is_never_one() -> None:
    result = fractions(presets.get("pcg-lcg64"), 15635871386175874928, 1)
    assert 0.0 <= result.values[0] < 1.0
