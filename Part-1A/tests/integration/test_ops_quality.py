"""Tests for the quality operation through lcgkit.ops.run (US7)."""

import pytest

from lcgkit.ops import run
from tests.helpers import error_of

pytestmark = [pytest.mark.ac("AC-054"), pytest.mark.fr("FR-028")]

BASE = {"preset": "minstd", "seed": 1, "sample_size": 100, "bins": 10}


def test_the_largest_sample_succeeds() -> None:
    answer = run("quality", {**BASE, "sample_size": 1_000_000})
    assert answer["verdict"] in {"no-defect-detected", "caution", "defect-detected"}


def test_a_sample_above_the_limit() -> None:
    error = error_of("quality", {**BASE, "sample_size": 1_000_001})
    assert error.code == "count-exceeds-limit"


@pytest.mark.parametrize("size", [1, 0, -1])
def test_a_sample_below_two(size: int) -> None:
    assert error_of("quality", {**BASE, "sample_size": size}).code == "invalid-count"


@pytest.mark.parametrize("bins", [0, 101, -1])
def test_bin_counts_outside_the_sample(bins: int) -> None:
    assert error_of("quality", {**BASE, "bins": bins}).code == "invalid-bins"
