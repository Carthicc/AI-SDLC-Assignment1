"""Layer 1: the structure of a reply, checked with lcgkit's own field table (task T006)."""

from __future__ import annotations

from typing import Any

from lcgkit import wire
from lcgkit.fields import COUNT, FIELDS, LARGE, LARGE_LIST, OPERATIONS, SIGNED_LARGE

SHAPES = {
    "call": {"decision", "operation", "arguments"},
    "clarify": {"decision", "question", "missing"},
    "refuse": {"decision", "reason", "message"},
}
REASONS = ("insecure-purpose", "out-of-scope", "unsafe-instruction")
MAX_TEXT_LENGTH = 300
GENERATOR_PARTS = {"m", "a", "c"}


def _violation(rule: str, detail: str) -> dict[str, str]:
    return {"rule": rule, "detail": detail}


def _kind_is_right(name: str, value: Any) -> bool:
    """True when `value` has the kind lcgkit's field table demands for `name`."""
    kind = FIELDS[name].kind
    if kind in (LARGE, SIGNED_LARGE):
        return isinstance(wire.decode_large(value, name, signed=kind == SIGNED_LARGE), int)
    if kind == COUNT:
        return type(value) is int
    if kind == LARGE_LIST:
        return isinstance(value, list) and all(
            isinstance(wire.decode_large(item, name), int) for item in value
        )
    return isinstance(value, str)


def _check_arguments(operation: str, arguments: Any) -> list[dict[str, str]]:
    """INV-03, INV-04 and INV-05 for the arguments of a call."""
    if not isinstance(arguments, dict):
        return [_violation("INV-03", "arguments is not an object")]
    allowed = OPERATIONS[operation].allowed
    found: list[dict[str, str]] = []
    for name, value in arguments.items():
        if name == "purpose" or name not in allowed:
            found.append(_violation("INV-03", f"argument {name!r} is not accepted by {operation}"))
        elif not _kind_is_right(name, value):
            found.append(_violation("INV-04", f"argument {name!r} has the wrong kind of value"))
    if "preset" in allowed:
        parts = GENERATOR_PARTS & arguments.keys()
        if ("preset" in arguments and parts) or (parts and parts != GENERATOR_PARTS):
            found.append(_violation("INV-05", "the generator must be a preset or all of a, c, m"))
    return found


def _check_call(reply: dict[str, Any]) -> list[dict[str, str]]:
    operation = reply.get("operation")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        return [_violation("INV-03", f"operation {operation!r} is not one of the nine")]
    return _check_arguments(operation, reply.get("arguments"))


def _text_is_right(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= MAX_TEXT_LENGTH


def _check_clarify(reply: dict[str, Any]) -> list[dict[str, str]]:
    found = []
    if not _text_is_right(reply.get("question")):
        found.append(_violation("INV-06", "question must be 1 to 300 characters"))
    missing = reply.get("missing")
    if not isinstance(missing, list) or not all(isinstance(item, str) for item in missing):
        found.append(_violation("INV-06", "missing must be a list of strings"))
    return found


def _check_refuse(reply: dict[str, Any]) -> list[dict[str, str]]:
    found = []
    if reply.get("reason") not in REASONS:
        found.append(_violation("INV-06", "reason is not one of the three allowed reasons"))
    if not _text_is_right(reply.get("message")):
        found.append(_violation("INV-06", "message must be 1 to 300 characters"))
    return found


def check_reply(reply: object) -> list[dict[str, str]]:
    """Return the structural violations of a reply (empty means layer 1 passes).

    Task: T006. Covers: INV-01 to INV-06, FR-022.
    """
    if not isinstance(reply, dict):
        return [_violation("INV-01", "the reply is not a single JSON object")]
    decision = reply.get("decision")
    if decision not in SHAPES:
        return [_violation("INV-01", f"decision {decision!r} is not call, clarify or refuse")]
    found = []
    if set(reply) != SHAPES[decision]:
        found.append(_violation("INV-02", f"fields {sorted(reply)} differ from {sorted(SHAPES[decision])}"))
    checks = {"call": _check_call, "clarify": _check_clarify, "refuse": _check_refuse}
    return found + checks[decision](reply)


def check_application_error(
    answer: dict[str, Any], expected_error: str, expected_calls: int | None
) -> list[dict[str, str]]:
    """Layer 1 for a case that expects only an application error.

    Task: T006. Covers: FR-022, FR-011.
    """
    found = []
    if answer.get("reply") is not None:
        found.append(_violation("INV-01", "the reply must be null for an application error"))
    error = answer.get("error")
    code = error.get("code") if isinstance(error, dict) else None
    if code != expected_error:
        found.append(_violation("INV-01", f"error code {code!r}, expected {expected_error!r}"))
    if expected_calls is not None and answer.get("model_calls") != expected_calls:
        found.append(_violation("INV-01", f"model_calls {answer.get('model_calls')!r}, expected {expected_calls}"))
    return found
