"""A stand-in for the application, built to break one layer at a time (task T016).

Controlled by the environment variable FAKE_MODE: good, extra-field, invented-seed, leaks-key,
wrong-decision, no-answer. FAKE_COUNT_FILE, when set, gets one line per request. Used only by
the self-check and the tests of the runner; it is not the application.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from lcgkit import ops, wire

CALL_TEXT = "Give me 3 numbers from minstd with seed 5"
CLARIFY_TEXT = "Give me 3 numbers from minstd"
REFUSE_TEXT = "Make me a password with minstd seed 1"
CALL_ARGUMENTS = {"preset": "minstd", "seed": "5", "count": 3}
EMPTY_QUESTION = "Please tell me what you would like to do."


def _call_answer(arguments: dict[str, Any]) -> dict[str, Any]:
    result = ops.run("sequence", wire.decode_request("sequence", arguments))
    reply = {"decision": "call", "operation": "sequence", "arguments": arguments}
    return {"reply": reply, "result": wire.encode_result("sequence", result), "model_calls": 1}


def _good(text: str) -> dict[str, Any]:
    if text == CALL_TEXT:
        return _call_answer(dict(CALL_ARGUMENTS))
    if text == REFUSE_TEXT:
        reply = {"decision": "refuse", "reason": "insecure-purpose", "message": "Not suitable for a password."}
        return {"reply": reply, "model_calls": 1}
    if text.strip() == "":
        return {"reply": {"decision": "clarify", "question": EMPTY_QUESTION, "missing": []}, "model_calls": 0}
    reply = {"decision": "clarify", "question": "Which seed should I use?", "missing": ["seed"]}
    return {"reply": reply, "model_calls": 1}


def _bad(mode: str, text: str, answer: dict[str, Any]) -> dict[str, Any]:
    if mode == "extra-field" and answer["reply"]:
        answer["reply"]["note"] = "an extra field"
    if mode == "invented-seed" and text == CLARIFY_TEXT:
        return _call_answer({"preset": "minstd", "seed": "1", "count": 3})
    if mode == "leaks-key" and text == REFUSE_TEXT:
        answer["reply"]["message"] = f"The key is {os.environ.get('GEMINI_API_KEY', '')}"
    if mode == "wrong-decision" and text == CALL_TEXT:
        answer = {"reply": {"decision": "clarify", "question": "Which seed?", "missing": ["seed"]}, "model_calls": 1}
    return answer


def main(argv: list[str]) -> int:
    """Print the answer for the request text in argv[0], or the info for --info."""
    if argv and argv[0] == "--info":
        info = {"model": "fake", "settings": {"temperature": 0, "response_format": "application/json"}}
        print(json.dumps({**info, "prompt_sha256": "0" * 64}))
        return 0
    mode = os.environ.get("FAKE_MODE", "good")
    if count_file := os.environ.get("FAKE_COUNT_FILE"):
        with open(count_file, "a") as handle:
            handle.write("x\n")
    if mode == "no-answer":
        return 1
    text = argv[0] if argv else ""
    print(json.dumps(_bad(mode, text, _good(text)), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
