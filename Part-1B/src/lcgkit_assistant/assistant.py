"""The flow for one request text: rules, the model, the contract check and lcgkit."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any, Protocol

from lcgkit import ops, wire
from lcgkit.errors import LcgError

from lcgkit_assistant import config
from lcgkit_assistant.contract import check_reply
from lcgkit_assistant.model import GeminiClient, ModelResult, ModelUnavailable


class Client(Protocol):
    """Anything that turns a request text into a model result."""

    def generate(self, text: str) -> ModelResult:
        """Return the model's reply for `text`."""


def _failure(code: str, message: str, calls: int, **extra: Any) -> dict[str, Any]:
    return {
        "reply": None,
        "error": {"code": code, "message": message},
        "model_calls": calls,
        **extra,
    }


def _empty_text_answer() -> dict[str, Any]:
    reply = {"decision": "clarify", "question": config.EMPTY_TEXT_QUESTION, "missing": []}
    return {"reply": reply, "model_calls": 0}


def _parse_object(text: str | None) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text or "")
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _run_call(reply: dict[str, Any], calls: int) -> dict[str, Any]:
    """Run a valid `call` reply through lcgkit; a rejection is reported, never retried."""
    operation, answer = reply["operation"], {"reply": reply, "model_calls": calls}
    try:
        request = wire.decode_request(operation, reply["arguments"])
        answer["result"] = wire.encode_result(operation, ops.run(operation, request))
    except LcgError as error:
        answer["error"] = {"code": error.code, "message": error.message}
    return answer


def _interpret(model: ModelResult) -> dict[str, Any]:
    reply = _parse_object(model.text)
    if reply is None:
        message = "the model's reply was not a JSON object"
        return _failure("reply-not-json", message, model.calls, raw=model.text or "")
    violations = check_reply(reply)
    if violations:
        message = "the reply broke the contract: " + ", ".join(violations)
        return {
            "reply": reply,
            "error": {"code": "invalid-reply", "message": message},
            "model_calls": model.calls,
        }
    if reply["decision"] == "call":
        return _run_call(reply, model.calls)
    return {"reply": reply, "model_calls": model.calls}


def handle(
    text: str, client: Client | None = None, environ: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Handle one request text and return the answer.

    The rules apply in this order: emptiness, length, key.

    Task: T044. Covers: FR-001, FR-002, FR-011, FR-012, FR-015, AC-032, AC-033, AC-053.
    """
    if not text.strip():
        return _empty_text_answer()
    if len(text) > config.MAX_TEXT_LENGTH:
        message = f"the request is longer than {config.MAX_TEXT_LENGTH} characters"
        return _failure("request-too-long", message, 0)
    if client is None:
        key = (os.environ if environ is None else environ).get(config.KEY_VARIABLE)
        if not key:
            return _failure("missing-api-key", f"{config.KEY_VARIABLE} is not set", 0)
        client = GeminiClient(key)
    try:
        return _interpret(client.generate(text))
    except ModelUnavailable as error:
        return _failure("model-unavailable", str(error), error.calls)
