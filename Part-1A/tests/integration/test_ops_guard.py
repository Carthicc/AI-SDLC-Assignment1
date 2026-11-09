"""Tests for the purpose guard through lcgkit.ops.run (US6)."""

import pytest
from lcgkit.ops import run

from tests.helpers import error_of

pytestmark = [pytest.mark.fr("FR-023"), pytest.mark.fr("FR-024")]

SEQUENCE = {"preset": "minstd", "seed": 1, "count": 3}
JUMP = {"preset": "minstd", "state": 1, "steps": 10}
STREAMS = {"preset": "minstd", "seed": 1, "streams": 2, "length": 3}
NO_PURPOSE = {
    "validate": {"preset": "minstd"},
    "quality": {"preset": "minstd", "seed": 1, "sample_size": 100, "bins": 10},
    "predict": {"outputs": [6, 1, 8], "m": 16},
}


@pytest.mark.ac("AC-044")
@pytest.mark.parametrize("label", ["token", "Session Token", "KEYS", "api-key"])
def test_sequence_refuses_insecure_purposes(label: str) -> None:
    assert error_of("sequence", {**SEQUENCE, "purpose": label}).code == "insecure-purpose"


@pytest.mark.ac("AC-045")
def test_a_harmless_purpose_goes_through() -> None:
    assert len(run("sequence", {**SEQUENCE, "purpose": "dice"})["outputs"]) == 3


@pytest.mark.ac("AC-047")
@pytest.mark.parametrize(("operation", "request_body"), [("jump", JUMP), ("streams", STREAMS)])
def test_jump_and_streams_refuse_password(operation: str, request_body: dict[str, object]) -> None:
    assert error_of(operation, {**request_body, "purpose": "password"}).code == "insecure-purpose"


@pytest.mark.ac("AC-047")
@pytest.mark.parametrize("operation", list(NO_PURPOSE))
def test_validate_quality_and_predict_take_no_purpose(operation: str) -> None:
    error = error_of(operation, {**NO_PURPOSE[operation], "purpose": "dice"})
    assert (error.code, error.field) == ("malformed-request", "purpose")


@pytest.mark.ac("AC-047")
def test_input_errors_come_before_the_purpose_refusal() -> None:
    error = error_of("sequence", {**SEQUENCE, "seed": -1, "purpose": "token"})
    assert error.code == "invalid-seed"
