"""The check of a model reply against the contract (FR-012)."""

from __future__ import annotations

from typing import Any

from lcgkit import wire
from lcgkit.fields import COUNT, FIELDS, LARGE, LARGE_LIST, OPERATIONS, SIGNED_LARGE

from lcgkit_assistant.config import MAX_FIELD_TEXT, REFUSAL_REASONS

SHAPES = {
    "call": frozenset({"decision", "operation", "arguments"}),
    "clarify": frozenset({"decision", "question", "missing"}),
    "refuse": frozenset({"decision", "reason", "message"}),
}
GENERATOR_PARTS = frozenset({"a", "c", "m"})
FORBIDDEN_ARGUMENT = "purpose"


def _kind_is_right(name: str, value: Any) -> bool:
    """True when `value` has the kind that lcgkit's field table demands for `name`."""
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


def _generator_is_wrong(allowed: frozenset[str], arguments: dict[str, Any]) -> bool:
    if "preset" not in allowed:
        return False
    parts = GENERATOR_PARTS & arguments.keys()
    return ("preset" in arguments and bool(parts)) or (bool(parts) and parts != GENERATOR_PARTS)


def _check_call(reply: dict[str, Any]) -> list[str]:
    operation, arguments = reply.get("operation"), reply.get("arguments")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        return ["INV-03"]
    if not isinstance(arguments, dict):
        return ["INV-03"]
    allowed = OPERATIONS[operation].allowed
    found = []
    for name, value in arguments.items():
        if name == FORBIDDEN_ARGUMENT or name not in allowed:
            found.append("INV-03")
        elif not _kind_is_right(name, value):
            found.append("INV-04")
    if _generator_is_wrong(allowed, arguments):
        found.append("INV-05")
    return found


def _text_is_right(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= MAX_FIELD_TEXT


def _check_clarify(reply: dict[str, Any]) -> list[str]:
    missing = reply.get("missing")
    missing_ok = isinstance(missing, list) and all(isinstance(item, str) for item in missing)
    return [] if _text_is_right(reply.get("question")) and missing_ok else ["INV-06"]


def _check_refuse(reply: dict[str, Any]) -> list[str]:
    reason_ok = reply.get("reason") in REFUSAL_REASONS
    return [] if reason_ok and _text_is_right(reply.get("message")) else ["INV-06"]


def check_reply(reply: object) -> list[str]:
    """Return the names of the violated rules INV-01 to INV-06 (empty if the reply is valid).

    Task: T042. Covers: FR-002, FR-012, INV-01, INV-02, INV-03, INV-04, INV-05, INV-06.
    """
    decision = reply.get("decision") if isinstance(reply, dict) else None
    if not isinstance(reply, dict) or not isinstance(decision, str) or decision not in SHAPES:
        return ["INV-01"]
    found = ["INV-02"] if set(reply) != SHAPES[decision] else []
    checks = {"call": _check_call, "clarify": _check_clarify, "refuse": _check_refuse}
    return list(dict.fromkeys(found + checks[decision](reply)))
