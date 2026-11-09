"""The field table: names, kinds, checking order and value rules, shared by every interface."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from lcgkit.errors import LcgError

MAX_COUNT = 1_000_000
MIN_MODULUS = 2
MAX_MODULUS = 2**64
MIN_SAMPLE_SIZE = 2
MAX_STEPS = 2**64
DEFAULT_K = 10

LARGE = "large"
SIGNED_LARGE = "signed-large"
COUNT = "count"
TEXT = "text"
LARGE_LIST = "large-list"

Rule = Callable[[Any, Mapping[str, Any]], None]


@dataclass(frozen=True)
class Field:
    """A request field: its name and its kind (how it travels in JSON and how it is typed)."""

    name: str
    kind: str


@dataclass(frozen=True)
class Operation:
    """What one operation accepts, in the order its fields are checked."""

    name: str
    uses_params: bool
    start: str | None
    own: tuple[str, ...]
    purpose: bool
    optional: frozenset[str]

    @property
    def order(self) -> tuple[str, ...]:
        """The fields after the generator parameters, in checking order."""
        return (() if self.start is None else (self.start,)) + self.own

    @property
    def allowed(self) -> frozenset[str]:
        """Every field name the operation accepts."""
        names = set(self.order)
        if self.uses_params:
            names |= {"preset", "m", "a", "c"}
        if self.purpose:
            names.add("purpose")
        return frozenset(names)


def error(code: str, field: str, message: str) -> LcgError:
    """Build an LcgError naming a field."""
    return LcgError(code, message, field)


def _modulus(value: int, seen: Mapping[str, Any]) -> None:
    if not MIN_MODULUS <= value <= MAX_MODULUS:
        raise error("invalid-modulus", "m", f"m must be from {MIN_MODULUS} to 2^64")


def _below_modulus(code: str, field: str) -> Rule:
    def rule(value: int, seen: Mapping[str, Any]) -> None:
        modulus = seen.get("m")
        if modulus is not None and not 0 <= value < modulus:
            raise error(code, field, f"{field} must be from 0 to m - 1")

    return rule


def _count(minimum: int, low_code: str, field: str) -> Rule:
    def rule(value: int, seen: Mapping[str, Any]) -> None:
        if value < minimum:
            raise error(low_code, field, f"{field} must be at least {minimum}")
        if value > MAX_COUNT:
            raise error("count-exceeds-limit", field, f"{field} must be at most {MAX_COUNT}")

    return rule


def _hi(value: int, seen: Mapping[str, Any]) -> None:
    low = seen["lo"]
    if low > value:
        raise error("invalid-range", "hi", "lo must not be greater than hi")
    if value - low + 1 > seen["m"]:
        raise error("range-exceeds-modulus", "hi", "the range holds more values than m")


def _bins(value: int, seen: Mapping[str, Any]) -> None:
    if not 1 <= value <= seen["sample_size"]:
        raise error("invalid-bins", "bins", "bins must be from 1 to the sample size")


def _steps(value: int, seen: Mapping[str, Any]) -> None:
    if not 0 <= value < MAX_STEPS:
        raise error("invalid-jump", "steps", "steps must be from 0 to 2^64 - 1")


def _streams(value: int, seen: Mapping[str, Any]) -> None:
    if value < 1:
        raise error("invalid-count", "streams", "streams must be at least 1")


def _length(value: int, seen: Mapping[str, Any]) -> None:
    if value < 1:
        raise error("invalid-count", "length", "length must be at least 1")
    total = seen["streams"] * value
    if total > MAX_COUNT:
        message = f"streams x length must be at most {MAX_COUNT}"
        raise error("count-exceeds-limit", "length", message)
    if total > seen["m"]:
        raise error("stream-exceeds-modulus", "length", "streams x length must not exceed m")


def _outputs(value: list[int], seen: Mapping[str, Any]) -> None:
    if not value:
        raise error("insufficient-data", "outputs", "at least one output is needed")
    if len(value) > MAX_COUNT:
        raise error("count-exceeds-limit", "outputs", f"at most {MAX_COUNT} outputs")
    if min(value) < 0:
        raise error("invalid-type", "outputs", "outputs must be non-negative integers")


def _hidden_bits(value: int, seen: Mapping[str, Any]) -> None:
    if value < 0:
        raise error("unsupported-combination", "hidden_bits", "hidden_bits must not be negative")


FIELDS: Mapping[str, Field] = MappingProxyType(
    {
        f.name: f
        for f in (
            Field("preset", TEXT),
            Field("m", LARGE),
            Field("a", LARGE),
            Field("c", LARGE),
            Field("seed", LARGE),
            Field("state", LARGE),
            Field("count", COUNT),
            Field("lo", SIGNED_LARGE),
            Field("hi", SIGNED_LARGE),
            Field("steps", LARGE),
            Field("sample_size", COUNT),
            Field("bins", COUNT),
            Field("outputs", LARGE_LIST),
            Field("hidden_bits", COUNT),
            Field("k", COUNT),
            Field("streams", COUNT),
            Field("length", COUNT),
            Field("purpose", TEXT),
        )
    }
)

RULES: Mapping[str, Rule] = MappingProxyType(
    {
        "m": _modulus,
        "a": _below_modulus("invalid-multiplier", "a"),
        "c": _below_modulus("invalid-increment", "c"),
        "seed": _below_modulus("invalid-seed", "seed"),
        "state": _below_modulus("invalid-seed", "state"),
        "count": _count(0, "invalid-count", "count"),
        "hi": _hi,
        "steps": _steps,
        "sample_size": _count(MIN_SAMPLE_SIZE, "invalid-count", "sample_size"),
        "bins": _bins,
        "outputs": _outputs,
        "hidden_bits": _hidden_bits,
        "k": _count(1, "invalid-count", "k"),
        "streams": _streams,
        "length": _length,
    }
)

DEFAULTS: Mapping[str, int] = MappingProxyType({"k": DEFAULT_K, "hidden_bits": 0})

_PREDICT_OPTIONAL = frozenset({"m", "a", "c", "hidden_bits", "k"})

OPERATIONS: Mapping[str, Operation] = MappingProxyType(
    {
        op.name: op
        for op in (
            Operation("presets", False, None, (), False, frozenset()),
            Operation("sequence", True, "seed", ("count",), True, frozenset()),
            Operation("integers", True, "seed", ("lo", "hi", "count"), True, frozenset()),
            Operation("fractions", True, "seed", ("count",), True, frozenset()),
            Operation("jump", True, "state", ("steps",), True, frozenset()),
            Operation("streams", True, "seed", ("streams", "length"), True, frozenset()),
            Operation("validate", True, None, (), False, frozenset()),
            Operation("quality", True, "seed", ("sample_size", "bins"), False, frozenset()),
            Operation(
                "predict", False, None,
                ("outputs", "m", "a", "c", "hidden_bits", "k"), False, _PREDICT_OPTIONAL,
            ),
        )
    }
)


def check_type(field: Field, value: object) -> None:
    """Raise `invalid-type` unless `value` has the right Python type for the field's kind.

    Task: T057. Covers: FR-001.
    """
    if field.kind == TEXT:
        good = isinstance(value, str)
    elif field.kind == LARGE_LIST:
        good = isinstance(value, list | tuple) and all(type(v) is int for v in value)
    else:
        good = type(value) is int
    if not good:
        raise error("invalid-type", field.name, f"{field.name} has the wrong type")
