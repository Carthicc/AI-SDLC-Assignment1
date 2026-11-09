"""Conversion between JSON and native values: decimal strings for large integers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from lcgkit.errors import LcgError
from lcgkit.fields import COUNT, FIELDS, LARGE, LARGE_LIST, OPERATIONS, SIGNED_LARGE

UNSIGNED_DECIMAL = re.compile(r"0|[1-9][0-9]*")
SIGNED_DECIMAL = re.compile(r"0|-?[1-9][0-9]*")
# Result keys whose integers can exceed 2**53 and are therefore written as decimal strings.
LARGE_RESULT_KEYS = frozenset(
    {
        "outputs", "values", "next_state", "state", "start_state", "predictions", "modulus",
        "a", "c", "m", "expected_period", "measured_period",
    }
)


@dataclass(frozen=True)
class InvalidField:
    """A value that could not be read; the error is raised when the field's turn comes."""

    field: str
    code: str


def decode_large(value: object, field: str, signed: bool = False) -> int | InvalidField:
    """Read a decimal string as an integer; anything else is marked, not raised.

    Task: T058. Covers: FR-001, FR-035.
    """
    pattern = SIGNED_DECIMAL if signed else UNSIGNED_DECIMAL
    if not isinstance(value, str) or not pattern.fullmatch(value):
        return InvalidField(field, "invalid-type")
    try:
        return int(value)
    except ValueError:  # more digits than Python converts: oversized
        return InvalidField(field, "invalid-type")


def encode_large(number: int) -> str:
    """Write an integer as a decimal string.

    Task: T058. Covers: FR-033.
    """
    return str(number)


def _decode_list(value: object, field: str) -> list[int] | InvalidField:
    if not isinstance(value, list):
        return InvalidField(field, "invalid-type")
    items = [decode_large(item, field) for item in value]
    numbers = [item for item in items if isinstance(item, int)]
    return numbers if len(numbers) == len(items) else InvalidField(field, "invalid-type")


def _decode_field(name: str, value: object) -> object:
    kind = FIELDS[name].kind
    if kind in (LARGE, SIGNED_LARGE):
        return decode_large(value, name, signed=kind == SIGNED_LARGE)
    if kind == COUNT:
        return value if type(value) is int else InvalidField(name, "invalid-type")
    if kind == LARGE_LIST:
        return _decode_list(value, name)
    return value


def decode_request(operation: str, body: object) -> dict[str, object]:
    """Turn a parsed JSON request into native values, marking unreadable ones.

    Structural problems (not an object, unknown operation or field) are raised at once.

    Task: T058. Covers: FR-001, FR-035, FR-036.
    """
    spec = OPERATIONS.get(operation)
    if spec is None:
        raise LcgError("malformed-request", f"unknown operation: {operation}")
    if not isinstance(body, dict):
        raise LcgError("malformed-request", "the request must be a JSON object")
    for name in body:
        if name not in spec.allowed:
            raise LcgError("malformed-request", f"unknown field: {name}", str(name))
    return {name: _decode_field(name, value) for name, value in body.items()}


def _encode(value: Any, large: bool) -> Any:
    if isinstance(value, dict):
        return {str(k): _encode(v, str(k) in LARGE_RESULT_KEYS) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_encode(item, large) for item in value]
    if large and type(value) is int:
        return encode_large(value)
    return value


def encode_result(operation: str, result: dict[str, Any]) -> dict[str, Any]:
    """Convert every large integer in a result to a decimal string, leaving the rest alone.

    Task: T058. Covers: FR-033, FR-035.
    """
    encoded: dict[str, Any] = _encode(result, False)
    return encoded
