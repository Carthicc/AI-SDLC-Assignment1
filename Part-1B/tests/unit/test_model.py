"""The Gemini client, with a fake transport and a fake sleep."""

import json

import pytest

from lcgkit_assistant import config
from lcgkit_assistant.model import GeminiClient, ModelUnavailable
from tests.conftest import fake_transport

KEY = "FAKE-KEY-0123456789"


def ok(text='{"decision": "clarify"}'):
    body = {"candidates": [{"content": {"parts": [{"text": text}]}}]}
    return 200, {}, json.dumps(body).encode()


def failure(status, headers=None):
    return status, headers or {}, b"{}"


def client(responses):
    sleeps = []
    transport = fake_transport(responses)
    return GeminiClient(KEY, transport=transport, sleep=sleeps.append), transport, sleeps


@pytest.mark.fr("FR-014")
@pytest.mark.fr("FR-015")
def test_the_request_is_built_as_specified():
    gemini, transport, _ = client([ok()])
    result = gemini.generate("Give me 5 numbers")
    url, headers, body, timeout = transport.calls[0]
    assert url.endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert headers["x-goog-api-key"] == KEY
    assert KEY not in url
    assert timeout == config.CALL_TIMEOUT_SECONDS
    sent = json.loads(body)
    assert sent["generationConfig"]["temperature"] == 0
    assert sent["generationConfig"]["responseMimeType"] == "application/json"
    assert sent["systemInstruction"]["parts"][0]["text"] == config.prompt_path().read_text()
    assert "Give me 5 numbers" in json.dumps(sent["contents"])
    assert result.text == '{"decision": "clarify"}'
    assert result.calls == 1


@pytest.mark.fr("FR-014")
def test_a_rate_limit_is_retried_after_five_seconds():
    gemini, _, sleeps = client([failure(429), ok()])
    result = gemini.generate("x")
    assert (result.calls, sleeps) == (2, [5])


@pytest.mark.fr("FR-014")
def test_retry_after_overrides_the_default_wait():
    gemini, _, sleeps = client([failure(429, {"Retry-After": "7"}), ok()])
    gemini.generate("x")
    assert sleeps == [7]


@pytest.mark.fr("FR-014")
def test_three_server_errors_then_success_waits_5_15_and_45():
    gemini, _, sleeps = client([failure(503)] * 3 + [ok()])
    result = gemini.generate("x")
    assert (result.calls, sleeps) == (4, [5, 15, 45])


@pytest.mark.fr("FR-014")
@pytest.mark.ac("AC-054")
def test_four_failures_raise_model_unavailable_without_the_key():
    gemini, _, _ = client([failure(503)] * 4)
    with pytest.raises(ModelUnavailable) as caught:
        gemini.generate("x")
    assert caught.value.calls == 4
    assert KEY not in str(caught.value)


@pytest.mark.fr("FR-014")
def test_other_statuses_are_not_retried():
    gemini, transport, sleeps = client([failure(400)])
    with pytest.raises(ModelUnavailable) as caught:
        gemini.generate("x")
    assert (caught.value.calls, len(transport.calls), sleeps) == (1, 1, [])


@pytest.mark.fr("FR-014")
@pytest.mark.ac("AC-047")
def test_a_timeout_is_a_retryable_failure():
    gemini, _, sleeps = client([TimeoutError("slow"), ok()])
    assert gemini.generate("x").calls == 2
    assert sleeps == [5]
    gemini, _, _ = client([TimeoutError("slow")] * 4)
    with pytest.raises(ModelUnavailable) as caught:
        gemini.generate("x")
    assert caught.value.calls == 4
