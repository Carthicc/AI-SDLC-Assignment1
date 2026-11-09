"""Tests for the sequence operation through lcgkit.ops.run (US1)."""

import pytest
from lcgkit.ops import run

from tests.conftest import canonical
from tests.helpers import GLIBC, error_of

pytestmark = [
    pytest.mark.fr("FR-001"),
    pytest.mark.fr("FR-004"),
    pytest.mark.fr("FR-005"),
    pytest.mark.fr("FR-006"),
]

WORKED = {"a": 5, "c": 3, "m": 16, "seed": 7, "count": 5}


@pytest.mark.ac("AC-004")
def test_count_limit() -> None:
    request = {**GLIBC, "seed": 1, "count": 1_000_000}
    assert len(run("sequence", request)["outputs"]) == 1_000_000
    assert error_of("sequence", {**request, "count": 1_000_001}).code == "count-exceeds-limit"


@pytest.mark.ac("AC-004")
def test_negative_count() -> None:
    assert error_of("sequence", {**WORKED, "count": -1}).code == "invalid-count"


@pytest.mark.ac("AC-005")
@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"m": 1, "a": 0, "c": 0, "seed": 0}, "invalid-modulus"),
        ({"m": 2**64 + 1, "a": 0, "c": 0, "seed": 0}, "invalid-modulus"),
        ({"a": 16}, "invalid-multiplier"),
        ({"c": -1}, "invalid-increment"),
        ({"seed": 16}, "invalid-seed"),
    ],
)
def test_invalid_parameters(change: dict[str, int], code: str) -> None:
    assert error_of("sequence", {**WORKED, **change}).code == code


@pytest.mark.ac("AC-006")
@pytest.mark.parametrize("field", ["m", "a", "c", "seed", "count"])
@pytest.mark.parametrize("bad", [3.5, "abc", True, None])
def test_wrong_type_names_the_field(field: str, bad: object) -> None:
    error = error_of("sequence", {**WORKED, field: bad})
    assert error.code == "invalid-type"
    assert error.field == field


@pytest.mark.ac("AC-007")
def test_only_the_first_error_is_reported() -> None:
    assert error_of("sequence", {**WORKED, "m": 1, "seed": 16}).code == "invalid-modulus"
    request = {**WORKED, "a": 16, "seed": 16}
    assert error_of("sequence", request).code == "invalid-multiplier"
    request = {**WORKED, "m": "x", "count": -1}
    error = error_of("sequence", request)
    assert (error.code, error.field) == ("invalid-type", "m")


@pytest.mark.ac("AC-009")
def test_one_hundred_identical_requests_give_identical_answers() -> None:
    first = canonical(run("sequence", WORKED))
    assert all(canonical(run("sequence", WORKED)) == first for _ in range(100))


@pytest.mark.ac("AC-010")
def test_every_success_says_it_is_not_secure() -> None:
    assert run("sequence", WORKED)["cryptographically_secure"] is False
