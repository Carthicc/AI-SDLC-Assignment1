"""The command line: output, exit status, --info and the key never being printed."""

import hashlib
import json
from pathlib import Path

import pytest

from lcgkit_assistant.cli import main
from lcgkit_assistant.model import ModelResult, ModelUnavailable
from tests.conftest import FakeClient, call_reply, clarify_reply, refuse_reply

KEY = "FAKE-KEY-0123456789"
ENV = {"GEMINI_API_KEY": KEY}
PROMPT = Path(__file__).parents[2] / "prompts" / "system.md"


def said(reply):
    return ModelResult(text=json.dumps(reply), calls=1)


def run(capsys, argv, client=None, environ=None):
    status = main(argv, client=client, environ=ENV if environ is None else environ)
    captured = capsys.readouterr()
    return status, captured.out, captured.err


@pytest.mark.fr("FR-013")
def test_the_answer_is_one_line_of_json_with_sorted_keys(capsys):
    status, out, _ = run(capsys, ["t"], FakeClient(said(call_reply())))
    assert status == 0
    assert out.count("\n") == 1
    answer = json.loads(out)
    assert out.strip() == json.dumps(answer, sort_keys=True)


@pytest.mark.ac("AC-056")
@pytest.mark.parametrize(
    "reply",
    [call_reply(), clarify_reply(), refuse_reply(), call_reply("predict", outputs=["5", "8"])],
)
def test_exit_status_is_zero_when_an_answer_was_produced(capsys, reply):
    assert run(capsys, ["t"], FakeClient(said(reply)))[0] == 0


@pytest.mark.ac("AC-056")
@pytest.mark.fr("FR-013")
@pytest.mark.parametrize(
    ("argv", "client", "environ"),
    [
        (["x" * 1001], FakeClient(), None),
        (["hello"], None, {}),
        (["t"], FakeClient(ModelUnavailable("down", 4)), None),
        (["t"], FakeClient(ModelResult(text="sorry", calls=1)), None),
        (["t"], FakeClient(said(call_reply("generate", seed="1"))), None),
    ],
    ids=[
        "request-too-long",
        "missing-api-key",
        "model-unavailable",
        "reply-not-json",
        "invalid-reply",
    ],
)
def test_exit_status_is_two_for_an_application_error(capsys, argv, client, environ):
    status, out, _ = run(capsys, argv, client, environ)
    assert status == 2
    assert json.loads(out)["error"]["code"]


@pytest.mark.ac("AC-061")
def test_info_needs_no_client_and_no_key(capsys):
    status, out, _ = run(capsys, ["--info"], None, {})
    info = json.loads(out)
    assert status == 0
    assert info["model"] == "gemini-3.5-flash-lite"
    assert info["settings"] == {"temperature": 0, "response_format": "application/json"}
    assert info["prompt_sha256"] == hashlib.sha256(PROMPT.read_bytes()).hexdigest()


@pytest.mark.ac("AC-054")
@pytest.mark.fr("FR-015")
def test_the_key_is_never_printed_even_when_the_model_fails(capsys):
    for client in (FakeClient(ModelUnavailable("down", 4)), FakeClient(said(call_reply()))):
        _, out, err = run(capsys, ["t"], client)
        assert KEY not in out + err
