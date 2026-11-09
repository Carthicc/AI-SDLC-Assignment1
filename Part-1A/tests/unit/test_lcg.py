"""Tests for lcgkit.core.lcg: ParameterSet, step and sequence (US1)."""

import pytest
from lcgkit.core.lcg import ParameterSet, sequence, step

pytestmark = [
    pytest.mark.fr("FR-002"),
    pytest.mark.fr("FR-003"),
    pytest.mark.fr("FR-004"),
    pytest.mark.fr("FR-007"),
]

SMALL = ParameterSet(a=5, c=3, m=16)
PCG = ParameterSet(a=6364136223846793005, c=1442695040888963407, m=2**64)


def test_step_applies_the_recurrence() -> None:
    assert step(SMALL, 7) == 6
    assert step(SMALL, 15) == (5 * 15 + 3) % 16


@pytest.mark.ac("AC-001")
def test_worked_example_five_values() -> None:
    result = sequence(SMALL, 7, 5)
    assert list(result.outputs) == [6, 1, 8, 11, 10]
    assert result.next_state == 10
    assert result.outputs_consumed == 5


@pytest.mark.ac("AC-002")
def test_continuing_from_the_next_state_gives_the_same_sequence() -> None:
    first = sequence(SMALL, 7, 5)
    more = sequence(SMALL, first.next_state, 3)
    assert list(more.outputs) == [5, 12, 15]
    assert list(sequence(SMALL, 7, 8).outputs) == [6, 1, 8, 11, 10, 5, 12, 15]


@pytest.mark.ac("AC-003")
@pytest.mark.parametrize("seed", [0, 7, 15])
def test_count_zero_gives_nothing_and_keeps_the_seed(seed: int) -> None:
    result = sequence(SMALL, seed, 0)
    assert list(result.outputs) == []
    assert result.next_state == seed


@pytest.mark.ac("AC-008")
def test_no_overflow_at_the_64_bit_limit() -> None:
    result = sequence(PCG, 0, 2)
    assert list(result.outputs) == [1442695040888963407, 1876011003808476466]


@pytest.mark.ac("AC-012")
def test_zero_fixed_point_warning() -> None:
    result = sequence(ParameterSet(a=7, c=0, m=16), 0, 5)
    assert list(result.outputs) == [0, 0, 0, 0, 0]
    assert "zero-fixed-point" in result.warnings


@pytest.mark.ac("AC-012")
@pytest.mark.parametrize("multiplier", [0, 1])
def test_degenerate_multiplier_warning(multiplier: int) -> None:
    result = sequence(ParameterSet(a=multiplier, c=3, m=16), 5, 3)
    assert "degenerate-multiplier" in result.warnings


@pytest.mark.ac("AC-012")
def test_no_warnings_for_a_healthy_generator() -> None:
    assert list(sequence(SMALL, 7, 5).warnings) == []
