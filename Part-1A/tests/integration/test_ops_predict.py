"""Tests for the predict operation through lcgkit.ops.run (US10)."""

import pytest
from lcgkit.ops import run

from tests.helpers import GLIBC, GLIBC_FROM_ONE, error_of

pytestmark = [
    pytest.mark.fr("FR-004"),
    pytest.mark.fr("FR-041"),
    pytest.mark.fr("FR-044"),
    pytest.mark.fr("FR-045"),
]

NOTICE = "This prediction shows that the generator is not secure."
CASE_B_ADDITION = " Recovering the modulus is probable, not certain."
KNOWN_MODULUS = {"m": GLIBC["m"], "outputs": GLIBC_FROM_ONE[:5]}
MUSL = {"a": 6364136223846793005, "c": 1, "m": 2**64}
MINSTD = {"a": 16807, "c": 0, "m": 2**31 - 1}


@pytest.mark.ac("AC-075")
def test_ten_predictions_by_default_or_as_many_as_asked() -> None:
    assert len(run("predict", KNOWN_MODULUS)["predictions"]) == 10
    assert len(run("predict", {**KNOWN_MODULUS, "k": 3})["predictions"]) == 3


@pytest.mark.ac("AC-075")
def test_k_limits() -> None:
    assert error_of("predict", {**KNOWN_MODULUS, "k": 1_000_001}).code == "count-exceeds-limit"
    assert error_of("predict", {**KNOWN_MODULUS, "k": 0}).code == "invalid-count"


@pytest.mark.ac("AC-089")
def test_too_many_observed_outputs() -> None:
    error = error_of("predict", {"m": 16, "outputs": [0] * 1_000_001})
    assert error.code == "count-exceeds-limit"


@pytest.mark.ac("AC-081")
@pytest.mark.parametrize(
    "request_body",
    [
        {"outputs": [1, 2, 3, 4], "hidden_bits": 4},
        {**MUSL, "outputs": [1, 2, 3, 4], "hidden_bits": 33},
        {**GLIBC, "outputs": [1, 2, 3, 4], "hidden_bits": 21},
        {**MINSTD, "outputs": [1, 2, 3, 4], "hidden_bits": 4},
    ],
    ids=["unknown-parameters", "musl-33-hidden-bits", "21-hidden-bits", "modulus-not-power-of-two"],
)
def test_unsupported_truncated_requests(request_body: dict[str, object]) -> None:
    assert error_of("predict", request_body).code == "unsupported-combination"


@pytest.mark.ac("AC-081")
@pytest.mark.parametrize("field", ["a", "c"])
def test_a_or_c_without_hidden_bits_is_malformed(field: str) -> None:
    error = error_of("predict", {**KNOWN_MODULUS, field: GLIBC[field]})
    assert (error.code, error.field) == ("malformed-request", field)


def test_predict_takes_no_preset() -> None:
    request = {"preset": "glibc-type0", "hidden_bits": 16, "outputs": [1, 2, 3, 4]}
    error = error_of("predict", request)
    assert (error.code, error.field) == ("malformed-request", "preset")


@pytest.mark.ac("AC-083")
def test_every_success_says_the_generator_is_not_secure() -> None:
    case_a = run("predict", KNOWN_MODULUS)
    case_b = run("predict", {"outputs": GLIBC_FROM_ONE[:12]})
    visible = [value >> 16 for value in GLIBC_FROM_ONE[:4]]
    case_c = run("predict", {**GLIBC, "hidden_bits": 16, "outputs": visible})
    assert [r["case"] for r in (case_a, case_b, case_c)] == ["A", "B", "C"]
    assert case_a["notice"] == NOTICE
    assert case_b["notice"] == NOTICE + CASE_B_ADDITION
    assert case_c["notice"] == NOTICE
