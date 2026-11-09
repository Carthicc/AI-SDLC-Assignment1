"""Tests for the integers operation through lcgkit.ops.run (US5)."""

import time

import pytest
from lcgkit.ops import run

from tests.helpers import error_of

pytestmark = [pytest.mark.fr("FR-020"), pytest.mark.fr("FR-048")]

SMALL = {"a": 5, "c": 3, "m": 16, "seed": 7, "count": 5}
TIME_LIMIT_SECONDS = 5


@pytest.mark.ac("AC-039")
def test_lo_above_hi() -> None:
    assert error_of("integers", {**SMALL, "lo": 3, "hi": 1}).code == "invalid-range"


@pytest.mark.ac("AC-039")
def test_range_with_more_values_than_the_modulus() -> None:
    assert error_of("integers", {**SMALL, "lo": 0, "hi": 16}).code == "range-exceeds-modulus"
    assert run("integers", {**SMALL, "lo": 0, "hi": 15})["values"]


@pytest.mark.ac("AC-039")
@pytest.mark.parametrize("field", ["lo", "hi"])
@pytest.mark.parametrize("bad", [1.5, "a", True, None])
def test_non_integer_bounds(field: str, bad: object) -> None:
    request = {**SMALL, "lo": 0, "hi": 3, field: bad}
    error = error_of("integers", request)
    assert (error.code, error.field) == ("invalid-type", field)


@pytest.mark.ac("AC-087")
def test_a_stuck_generator_is_refused_instead_of_hanging() -> None:
    request = {"a": 1, "c": 0, "m": 16, "seed": 15, "count": 3, "lo": 1, "hi": 3}
    started = time.perf_counter()
    error = error_of("integers", request)
    assert time.perf_counter() - started < TIME_LIMIT_SECONDS
    assert (error.code, error.field) == ("unsupported-combination", "seed")
