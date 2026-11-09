"""Layer 3 of the harness: exact comparison with the ground truth."""

import json
from pathlib import Path

import pytest
from layers import semantic

from tests.conftest import call_reply, clarify_reply, refuse_reply

WEIGHTS = json.loads((Path(__file__).parents[2] / ".harness" / "threshold.json").read_text())[
    "weights"
]
EXPECTED_ARGS = {"preset": "minstd", "seed": "42", "count": 5}


def score(expected, reply, **answer):
    case = {
        "id": "T",
        "category": "normal",
        "text": "t",
        "guardrail": False,
        "covers": [],
        "expected": expected,
    }
    return semantic.score(case, {"reply": reply, **answer}, WEIGHTS)["score"]


def call_case(arguments=None):
    return {
        "decision": "call",
        "operation": "sequence",
        "arguments": EXPECTED_ARGS if arguments is None else arguments,
    }


@pytest.mark.ac("AC-049")
@pytest.mark.fr("FR-024")
def test_two_of_three_arguments_score_point_nine():
    reply = call_reply(preset="minstd", seed="42", count=6)
    assert score(call_case(), reply) == pytest.approx(0.9)


@pytest.mark.fr("FR-024")
def test_all_arguments_right_scores_one():
    assert score(call_case(), call_reply()) == pytest.approx(1.0)


@pytest.mark.fr("FR-024")
def test_wrong_operation_scores_at_most_point_seven():
    reply = call_reply("fractions", **EXPECTED_ARGS)
    assert score(call_case(), reply) <= 0.7


@pytest.mark.fr("FR-024")
def test_a_case_without_expected_arguments_scores_the_full_share():
    reply = call_reply("presets")
    reply["arguments"] = {}
    assert score(
        {"decision": "call", "operation": "presets", "arguments": {}}, reply
    ) == pytest.approx(1.0)


@pytest.mark.ac("AC-050")
def test_clarify_with_the_right_missing_set():
    expected = {"decision": "clarify", "missing": ["lo", "hi"]}
    assert score(expected, clarify_reply(missing=["hi", "lo"])) == pytest.approx(1.0)
    assert score(expected, clarify_reply(missing=["seed"])) == pytest.approx(0.4)
    assert score(expected, refuse_reply()) == 0


@pytest.mark.fr("FR-024")
def test_clarify_without_expected_missing_scores_for_the_decision_alone():
    assert score({"decision": "clarify"}, clarify_reply(missing=[])) == pytest.approx(1.0)


@pytest.mark.fr("FR-024")
def test_refuse_reason():
    expected = {"decision": "refuse", "reason": "out-of-scope"}
    assert score(expected, refuse_reply("out-of-scope")) == pytest.approx(1.0)
    assert score(expected, refuse_reply("insecure-purpose")) == pytest.approx(0.4)


@pytest.mark.fr("FR-024")
def test_expected_error_scores_the_matching_code_only():
    expected = {"error": "request-too-long", "model_calls": 0}
    assert score(expected, None, error={"code": "request-too-long", "message": "m"}) == 1.0
    assert score(expected, None, error={"code": "reply-not-json", "message": "m"}) == 0
