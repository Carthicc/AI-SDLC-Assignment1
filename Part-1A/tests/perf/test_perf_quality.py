"""Timing test for FR-008: the largest quality report within 15 seconds (US7)."""

import time

import pytest

from lcgkit.ops import run

pytestmark = [pytest.mark.perf, pytest.mark.ac("AC-056"), pytest.mark.fr("FR-008")]

LIMIT_SECONDS = 15
MODULUS = 2**24


def test_a_million_values_with_a_full_period_search() -> None:
    request = {"a": 1664525, "c": 1013904223 % MODULUS, "m": MODULUS, "seed": 1,
               "sample_size": 1_000_000, "bins": 1000}
    started = time.perf_counter()
    answer = run("quality", request)
    assert time.perf_counter() - started < LIMIT_SECONDS
    assert answer["measured_period"] == MODULUS
