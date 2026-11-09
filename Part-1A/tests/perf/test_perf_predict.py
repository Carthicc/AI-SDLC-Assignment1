"""Timing test for FR-008: the largest truncated-output search within 5 seconds (US10)."""

import time

import pytest

from lcgkit.ops import run
from tests.helpers import GLIBC, GLIBC_FROM_ONE

pytestmark = [pytest.mark.perf, pytest.mark.ac("AC-082"), pytest.mark.fr("FR-008")]

HIDDEN_BITS = 20
LIMIT_SECONDS = 5


def test_twenty_hidden_bits() -> None:
    visible = [value >> HIDDEN_BITS for value in GLIBC_FROM_ONE[:6]]
    request = {**GLIBC, "hidden_bits": HIDDEN_BITS, "outputs": visible}
    started = time.perf_counter()
    answer = run("predict", request)
    assert time.perf_counter() - started < LIMIT_SECONDS
    assert answer["case"] == "C"
