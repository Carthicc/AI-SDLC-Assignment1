"""Tests for the streams operation through lcgkit.ops.run (US11)."""

import pytest
from lcgkit.ops import run

from tests.helpers import GLIBC, GLIBC_FROM_ONE, error_of
from tests.oracle.reference import closed_form_state

pytestmark = [pytest.mark.fr("FR-004"), pytest.mark.fr("FR-046"), pytest.mark.fr("FR-047")]

REQUEST = {"preset": "glibc-type0", "seed": 1, "streams": 4, "length": 5}


@pytest.mark.ac("AC-084")
def test_joined_streams_equal_the_plain_sequence() -> None:
    streams = run("streams", REQUEST)["streams"]
    joined = [value for stream in streams for value in stream["outputs"]]
    assert joined == GLIBC_FROM_ONE


@pytest.mark.ac("AC-085")
def test_each_stream_starts_at_the_jump_ahead_state() -> None:
    streams = run("streams", REQUEST)["streams"]
    assert [stream["index"] for stream in streams] == [0, 1, 2, 3]
    for stream in streams:
        expected = closed_form_state(GLIBC["a"], GLIBC["c"], GLIBC["m"], 1, stream["index"] * 5)
        assert stream["start_state"] == expected


@pytest.mark.ac("AC-086")
def test_more_outputs_than_the_modulus() -> None:
    request = {"a": 5, "c": 3, "m": 16, "seed": 7, "streams": 4, "length": 5}
    assert error_of("streams", request).code == "stream-exceeds-modulus"


@pytest.mark.ac("AC-086")
@pytest.mark.parametrize("field", ["streams", "length"])
@pytest.mark.parametrize("value", [0, -1])
def test_zero_or_negative_counts(field: str, value: int) -> None:
    assert error_of("streams", {**REQUEST, field: value}).code == "invalid-count"


@pytest.mark.ac("AC-088")
def test_the_total_size_limit() -> None:
    too_big = {**REQUEST, "streams": 1001, "length": 1000}
    assert error_of("streams", too_big).code == "count-exceeds-limit"
    largest = run("streams", {**REQUEST, "streams": 1000, "length": 1000})
    assert len(largest["streams"]) == 1000
