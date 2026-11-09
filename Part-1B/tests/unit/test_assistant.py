"""The flow for one request text, with a fake client and no network (AC-057)."""

import json

import pytest
from lcgkit import ops, wire

from lcgkit_assistant import config
from lcgkit_assistant.assistant import handle
from lcgkit_assistant.model import ModelResult, ModelUnavailable
from tests.conftest import FakeClient, call_reply, clarify_reply, refuse_reply

KEY_ENV = {"GEMINI_API_KEY": "FAKE-KEY-0123456789"}


def said(reply, calls=1):
    return ModelResult(text=json.dumps(reply), calls=calls)


@pytest.mark.ac("AC-032")
@pytest.mark.fr("FR-011")
@pytest.mark.parametrize("text", ["", "   \n\t"])
def test_empty_text_gets_the_fixed_question_without_a_model_call(text):
    client = FakeClient()
    answer = handle(text, client=client, environ={})
    reply = answer["reply"]
    assert (reply["decision"], reply["missing"], answer["model_calls"]) == ("clarify", [], 0)
    assert reply["question"] == config.EMPTY_TEXT_QUESTION
    assert 1 <= len(reply["question"]) <= 300
    assert client.texts == []
    assert "error" not in answer


@pytest.mark.ac("AC-033")
@pytest.mark.fr("FR-011")
def test_over_long_text_is_rejected_and_the_limit_itself_is_accepted():
    client = FakeClient(said(clarify_reply()))
    answer = handle("x" * 1001, client=client, environ={})
    assert (answer["reply"], answer["error"]["code"], answer["model_calls"]) == (
        None,
        "request-too-long",
        0,
    )
    assert client.texts == []
    assert "error" not in handle("x" * 1000, client=client, environ={})


@pytest.mark.ac("AC-053")
@pytest.mark.fr("FR-015")
def test_a_missing_key_is_reported_without_a_model_call():
    answer = handle("Give me 5 numbers", environ={})
    assert (answer["reply"], answer["error"]["code"], answer["model_calls"]) == (
        None,
        "missing-api-key",
        0,
    )


@pytest.mark.fr("FR-011")
def test_the_rules_apply_in_the_order_emptiness_length_key():
    assert handle("", environ={})["reply"]["decision"] == "clarify"
    assert handle("x" * 1001, environ={})["error"]["code"] == "request-too-long"


@pytest.mark.ac("AC-010")
def test_a_call_is_run_through_lcgkit():
    arguments = {"preset": "minstd", "seed": "42", "count": 5}
    answer = handle("t", client=FakeClient(said(call_reply(**arguments))), environ=KEY_ENV)
    expected = wire.encode_result(
        "sequence", ops.run("sequence", wire.decode_request("sequence", arguments))
    )
    assert answer["result"] == expected
    assert expected["outputs"][0] == "705894"
    assert "error" not in answer
    assert answer["model_calls"] == 1


@pytest.mark.ac("AC-011")
def test_a_call_that_lcgkit_rejects_is_reported_not_retried():
    client = FakeClient(said(call_reply("predict", outputs=["5", "8"])))
    answer = handle("t", client=client, environ=KEY_ENV)
    assert answer["error"]["code"] == "insufficient-data"
    assert "result" not in answer
    assert (answer["model_calls"], len(client.texts)) == (1, 1)


@pytest.mark.fr("FR-012")
def test_text_that_is_not_json_is_reported_with_the_raw_text():
    answer = handle("t", client=FakeClient(ModelResult(text="sorry, no", calls=1)), environ=KEY_ENV)
    assert (answer["reply"], answer["raw"], answer["error"]["code"]) == (
        None,
        "sorry, no",
        "reply-not-json",
    )


@pytest.mark.ac("AC-055")
@pytest.mark.fr("FR-012")
@pytest.mark.parametrize(
    "reply", [call_reply("generate", seed="1"), {**refuse_reply(), "note": "x"}]
)
def test_an_invalid_reply_is_included_and_nothing_is_run(reply):
    client = FakeClient(said(reply))
    answer = handle("t", client=client, environ=KEY_ENV)
    assert answer["error"]["code"] == "invalid-reply"
    assert answer["reply"] == reply
    assert "result" not in answer
    assert len(client.texts) == 1


@pytest.mark.fr("FR-012")
@pytest.mark.parametrize("reply", [clarify_reply(), refuse_reply()])
def test_clarify_and_refuse_pass_through(reply):
    answer = handle("t", client=FakeClient(said(reply)), environ=KEY_ENV)
    assert answer == {"reply": reply, "model_calls": 1}


@pytest.mark.fr("FR-015")
def test_an_unavailable_model_is_reported_with_its_call_count():
    answer = handle("t", client=FakeClient(ModelUnavailable("down", 4)), environ=KEY_ENV)
    assert (answer["reply"], answer["error"]["code"], answer["model_calls"]) == (
        None,
        "model-unavailable",
        4,
    )


@pytest.mark.ac("AC-057")
@pytest.mark.fr("FR-029")
def test_result_and_error_are_never_both_present():
    replies = [
        call_reply(),
        call_reply("predict", outputs=["5", "8"]),
        clarify_reply(),
        refuse_reply(),
    ]
    for reply in replies:
        answer = handle("t", client=FakeClient(said(reply)), environ=KEY_ENV)
        assert not ("result" in answer and "error" in answer)
