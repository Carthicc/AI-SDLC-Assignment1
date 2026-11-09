"""Layer 1 of the harness (INV-01 to INV-06), written from the specification."""

import pytest
from layers import structure

from tests.conftest import call_reply, clarify_reply, refuse_reply


def rules(reply):
    return {v["rule"] for v in structure.check_reply(reply)}


@pytest.mark.fr("FR-022")
@pytest.mark.parametrize(
    "reply", [call_reply(), clarify_reply(), refuse_reply(), call_reply("presets", **{})]
)
def test_valid_replies_have_no_violations(reply):
    assert structure.check_reply(reply) == []


@pytest.mark.inv("INV-01")
@pytest.mark.parametrize("reply", ["text", None, [], {}, {"decision": "guess"}])
def test_inv01_reply_is_one_object_with_a_known_decision(reply):
    assert rules(reply) == {"INV-01"}


@pytest.mark.inv("INV-02")
def test_inv02_extra_and_missing_fields():
    assert rules({**refuse_reply(), "note": "x"}) == {"INV-02"}
    assert "INV-02" in rules({"decision": "clarify", "question": "Which seed?"})


@pytest.mark.inv("INV-03")
@pytest.mark.parametrize(
    "reply",
    [
        call_reply("generate", seed="1"),
        call_reply(preset="minstd", seed="1", count=5, purpose="game"),
        call_reply(preset="minstd", seed="1", count=5, colour="red"),
    ],
)
def test_inv03_operation_and_argument_names(reply):
    assert rules(reply) == {"INV-03"}


@pytest.mark.inv("INV-04")
@pytest.mark.parametrize(
    "arguments",
    [
        {"preset": "minstd", "seed": 42, "count": 5},
        {"preset": "minstd", "seed": "42", "count": "5"},
        {"preset": "minstd", "seed": "42", "count": True},
    ],
)
def test_inv04_argument_kinds(arguments):
    assert rules(call_reply(**arguments)) == {"INV-04"}


@pytest.mark.inv("INV-04")
def test_inv04_outputs_must_be_decimal_strings():
    assert rules(call_reply("predict", m="2147483648", outputs=[1, 2])) == {"INV-04"}


@pytest.mark.inv("INV-05")
@pytest.mark.parametrize(
    "arguments",
    [
        {"preset": "minstd", "a": "5", "c": "3", "m": "16", "seed": "1", "count": 2},
        {"a": "5", "c": "3", "seed": "1", "count": 2},
    ],
)
def test_inv05_generator_is_a_preset_or_all_three_parts(arguments):
    assert rules(call_reply(**arguments)) == {"INV-05"}


@pytest.mark.inv("INV-06")
@pytest.mark.parametrize(
    "reply",
    [
        clarify_reply(question=""),
        clarify_reply(missing=[1]),
        refuse_reply(message="x" * 301),
        refuse_reply(reason="boring"),
    ],
)
def test_inv06_text_fields_and_reason(reply):
    assert rules(reply) == {"INV-06"}


def answer(code="request-too-long", reply=None, calls=0):
    return {"reply": reply, "error": {"code": code, "message": "m"}, "model_calls": calls}


@pytest.mark.fr("FR-022")
def test_application_error_passes_for_the_expected_answer():
    assert structure.check_application_error(answer(), "request-too-long", 0) == []


@pytest.mark.fr("FR-022")
@pytest.mark.parametrize(
    "bad", [answer(reply=clarify_reply()), answer(code="reply-not-json"), answer(calls=1)]
)
def test_application_error_fails_for_a_different_answer(bad):
    assert structure.check_application_error(bad, "request-too-long", 0)
