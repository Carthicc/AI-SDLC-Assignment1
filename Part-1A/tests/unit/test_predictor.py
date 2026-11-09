"""Tests for lcgkit.core.predictor: predicting from observed outputs (US10)."""

import pytest
from lcgkit.core.lcg import ParameterSet
from lcgkit.core.predictor import predict_known_modulus, predict_truncated, predict_unknown_modulus
from lcgkit.errors import LcgError

from lcgkit.core import presets
from tests.oracle.reference import step_sequence

pytestmark = [
    pytest.mark.fr("FR-039"),
    pytest.mark.fr("FR-040"),
    pytest.mark.fr("FR-041"),
    pytest.mark.fr("FR-042"),
    pytest.mark.fr("FR-043"),
]

GLIBC = presets.get("glibc-type0")
PCG = presets.get("pcg-lcg64")
K = 10
HIDDEN = 16


def stream(p: ParameterSet, seed: int, count: int) -> list[int]:
    """The generator's outputs from `seed`, by the oracle."""
    return step_sequence(p.a, p.c, p.m, seed, count)


@pytest.mark.ac("AC-074")
def test_case_a_recovers_the_parameters_and_predicts() -> None:
    values = stream(GLIBC, 1, 5 + K)
    result = predict_known_modulus(GLIBC.m, values[:5], K)
    assert result.case == "A"
    assert (result.a, result.c) == (GLIBC.a, GLIBC.c)
    assert list(result.predictions) == values[5:]
    # FR-042: the recovered parameters reproduce every supplied output
    assert step_sequence(result.a, result.c, GLIBC.m, values[0], 4) == values[1:5]


@pytest.mark.ac("AC-076")
def test_case_a_with_two_outputs_has_too_little_data() -> None:
    with pytest.raises(LcgError) as info:
        predict_known_modulus(GLIBC.m, stream(GLIBC, 1, 2), K)
    assert info.value.code == "insufficient-data"


@pytest.mark.ac("AC-076")
def test_case_a_refuses_to_guess_when_many_multipliers_fit() -> None:
    with pytest.raises(LcgError) as info:
        predict_known_modulus(16, [0, 0, 0], K)
    assert info.value.code == "ambiguous-parameters"


@pytest.mark.ac("AC-077")
@pytest.mark.parametrize(("p", "seed"), [(GLIBC, 1), (PCG, 0)])
def test_case_b_recovers_the_modulus_and_predicts(p: ParameterSet, seed: int) -> None:
    values = stream(p, seed, 12 + K)
    result = predict_unknown_modulus(values[:12], K)
    assert result.case == "B"
    assert (result.modulus, result.a, result.c) == (p.m, p.a, p.c)
    assert list(result.predictions) == values[12:]
    # FR-042: the recovered parameters reproduce every supplied output
    assert step_sequence(result.a, result.c, result.modulus, values[0], 11) == values[1:12]


@pytest.mark.ac("AC-078")
@pytest.mark.parametrize(("p", "seed"), [(GLIBC, 1), (PCG, 0)])
def test_case_b_needs_twelve_outputs(p: ParameterSet, seed: int) -> None:
    with pytest.raises(LcgError) as info:
        predict_unknown_modulus(stream(p, seed, 11), K)
    assert info.value.code == "insufficient-data"


@pytest.mark.ac("AC-079")
def test_case_c_recovers_the_state_from_truncated_outputs() -> None:
    values = stream(GLIBC, 1, 4 + K)
    visible = [value >> HIDDEN for value in values[:4]]
    result = predict_truncated(GLIBC, HIDDEN, visible, K)
    assert result.case == "C"
    assert result.state == values[3]
    assert list(result.predictions) == values[4:]


@pytest.mark.ac("AC-080")
def test_case_c_with_two_outputs_is_ambiguous() -> None:
    visible = [value >> HIDDEN for value in stream(GLIBC, 1, 2)]
    with pytest.raises(LcgError) as info:
        predict_truncated(GLIBC, HIDDEN, visible, K)
    assert info.value.code == "ambiguous-parameters"
