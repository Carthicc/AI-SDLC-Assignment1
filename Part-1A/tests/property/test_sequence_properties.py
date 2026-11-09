"""Property tests for the sequence operation (US1)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from lcgkit.ops import run

from tests.conftest import canonical

pytestmark = [pytest.mark.ac("AC-002"), pytest.mark.fr("FR-003"), pytest.mark.fr("FR-005")]


@st.composite
def generators(draw: st.DrawFn) -> dict[str, int]:
    """A valid a, c, m and seed, with m anywhere from 2 to 2**64."""
    m = draw(st.integers(min_value=2, max_value=2**64))
    return {
        "m": m,
        "a": draw(st.integers(min_value=0, max_value=m - 1)),
        "c": draw(st.integers(min_value=0, max_value=m - 1)),
        "seed": draw(st.integers(min_value=0, max_value=m - 1)),
    }


@given(generators(), st.integers(0, 60), st.integers(0, 60))
def test_continuing_equals_one_longer_request(gen: dict[str, int], n1: int, n2: int) -> None:
    first = run("sequence", {**gen, "count": n1})
    more = run("sequence", {**gen, "seed": first["next_state"], "count": n2})
    whole = run("sequence", {**gen, "count": n1 + n2})
    assert first["outputs"] + more["outputs"] == whole["outputs"]


@given(generators(), st.integers(0, 60))
def test_same_request_same_answer_and_values_in_range(gen: dict[str, int], n: int) -> None:
    request = {**gen, "count": n}
    answer = run("sequence", request)
    assert canonical(answer) == canonical(run("sequence", request))
    assert all(0 <= value < gen["m"] for value in answer["outputs"])
