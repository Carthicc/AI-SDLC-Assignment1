"""Tests for the jump operation through lcgkit.ops.run (US4)."""

import pytest
from lcgkit.ops import run

from tests.helpers import GLIBC, error_of
from tests.oracle.reference import closed_form_state

pytestmark = [pytest.mark.ac("AC-033"), pytest.mark.fr("FR-017")]


def test_the_largest_distance_works() -> None:
    steps = 2**64 - 1
    answer = run("jump", {**GLIBC, "state": 1, "steps": steps})
    assert answer["state"] == closed_form_state(GLIBC["a"], GLIBC["c"], GLIBC["m"], 1, steps)


@pytest.mark.parametrize("steps", [2**64, -1])
def test_distances_out_of_range(steps: int) -> None:
    error = error_of("jump", {**GLIBC, "state": 1, "steps": steps})
    assert (error.code, error.field) == ("invalid-jump", "steps")
