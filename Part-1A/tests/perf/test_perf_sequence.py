"""Timing tests for FR-008: one million values within 5 seconds (US1)."""

import time

import pytest
from fastapi.testclient import TestClient

from lcgkit.ops import run
from lcgkit.service import app
from tests.helpers import GLIBC

pytestmark = [pytest.mark.perf, pytest.mark.ac("AC-011"), pytest.mark.fr("FR-008")]

LIMIT_SECONDS = 5
COUNT = 1_000_000


def test_library_one_million_values() -> None:
    started = time.perf_counter()
    result = run("sequence", {**GLIBC, "seed": 1, "count": COUNT})
    assert time.perf_counter() - started < LIMIT_SECONDS
    assert len(result["outputs"]) == COUNT


def test_service_one_million_values() -> None:
    body = {"a": str(GLIBC["a"]), "c": str(GLIBC["c"]), "m": str(GLIBC["m"]),
            "seed": "1", "count": COUNT}
    started = time.perf_counter()
    response = TestClient(app).post("/v1/sequence", json=body)
    assert time.perf_counter() - started < LIMIT_SECONDS
    assert response.status_code == 200
    assert len(response.json()["outputs"]) == COUNT
