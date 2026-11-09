"""The operations layer: one request path shared by the library, the command line and HTTP."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from lcgkit.core import bounded, guard, jump, lcg, presets, quality, streams, validator
from lcgkit.core.lcg import ParameterSet
from lcgkit.errors import LcgError
from lcgkit.fields import DEFAULTS, FIELDS, OPERATIONS, RULES, Operation, check_type
from lcgkit.wire import InvalidField

Handler = Callable[[Mapping[str, Any]], dict[str, Any]]
PARAMETER_FIELDS = ("m", "a", "c")
EXPLICIT_PARAMETERS = frozenset(PARAMETER_FIELDS)


def _malformed(message: str, field: str | None = None) -> LcgError:
    return LcgError("malformed-request", message, field)


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _check_conflicts(spec: Operation, request: Mapping[str, object]) -> None:
    """Reject a preset together with explicit parameters, and a or c without hidden bits."""
    if "preset" in request and EXPLICIT_PARAMETERS & request.keys():
        raise _malformed("give either a preset or a, c and m, not both", "preset")
    if spec.name == "predict" and not _positive(request.get("hidden_bits")):
        for name in ("a", "c"):
            if name in request:
                raise _malformed(f"{name} is only accepted with a positive hidden_bits", name)


def _check_structure(spec: Operation, request: Mapping[str, object]) -> None:
    """Report structural problems first: unknown, conflicting or missing fields."""
    for name in request:
        if name not in spec.allowed:
            raise _malformed(f"unknown field: {name}", str(name))
    _check_conflicts(spec, request)
    needed = [n for n in spec.order if n not in spec.optional]
    if spec.uses_params and "preset" not in request:
        needed = [*PARAMETER_FIELDS, *needed]
    for name in needed:
        if name not in request:
            raise _malformed(f"missing field: {name}", name)


def _take(name: str, request: Mapping[str, object], seen: dict[str, Any]) -> None:
    """Check one field's type and value (in that order) and keep it."""
    value = request[name]
    if isinstance(value, InvalidField):
        raise LcgError(value.code, f"{value.field} could not be read", value.field)
    check_type(FIELDS[name], value)
    rule = RULES.get(name)
    if rule is not None:
        rule(value, seen)
    seen[name] = value


def _parameters(request: Mapping[str, object], seen: dict[str, Any]) -> None:
    """Resolve a preset, or check m, a and c in that order."""
    if "preset" in request:
        _take("preset", request, seen)
        params = presets.get(seen.pop("preset"))
        seen.update(a=params.a, c=params.c, m=params.m)
        return
    for name in PARAMETER_FIELDS:
        _take(name, request, seen)


def _validate(spec: Operation, request: Mapping[str, object]) -> dict[str, Any]:
    """Check every field in the table's order; the first problem is the only one reported."""
    seen: dict[str, Any] = {}
    if spec.uses_params:
        _parameters(request, seen)
        seen["p"] = ParameterSet(seen["a"], seen["c"], seen["m"])
    for name in spec.order:
        if name in request:
            _take(name, request, seen)
        elif name in DEFAULTS:
            seen[name] = DEFAULTS[name]
    return seen


def _check_purpose(spec: Operation, request: Mapping[str, object]) -> None:
    """Apply the purpose guard last, once every other input is known to be valid."""
    if spec.purpose and "purpose" in request:
        seen: dict[str, Any] = {}
        _take("purpose", request, seen)
        guard.check_purpose(seen["purpose"])


def run(operation: str, request: Mapping[str, object]) -> dict[str, Any]:
    """Validate a request with the field table, run the operation and shape the answer.

    Task: T059. Covers: FR-001, FR-005, FR-006, FR-036.
    """
    spec = OPERATIONS.get(operation)
    if spec is None:
        raise _malformed(f"unknown operation: {operation}")
    if not isinstance(request, Mapping):
        raise _malformed("the request must be an object")
    _check_structure(spec, request)
    values = _validate(spec, request)
    _check_purpose(spec, request)
    result = HANDLERS[operation](values)
    return {**result, "cryptographically_secure": False}


def _sequence(v: Mapping[str, Any]) -> dict[str, Any]:
    """Task: T061. Covers: FR-001 to FR-008."""
    result = lcg.sequence(v["p"], v["seed"], v["count"])
    return {
        "outputs": result.outputs,
        "outputs_consumed": result.outputs_consumed,
        "next_state": result.next_state,
        "warnings": result.warnings,
    }


def _presets(v: Mapping[str, Any]) -> dict[str, Any]:
    """Task: T063. Covers: FR-010."""
    return {
        "presets": [
            {
                "name": item.name, "a": item.params.a, "c": item.params.c, "m": item.params.m,
                "description": item.description,
            }
            for item in presets.PRESETS.values()
        ]
    }


def _validate_handler(v: Mapping[str, Any]) -> dict[str, Any]:
    """Task: T066. Covers: FR-013, FR-014, FR-015."""
    verdict = validator.validate(v["p"])
    result: dict[str, Any] = {
        "verdict": verdict.verdict,
        "conditions": [{"name": c.name, "passed": c.passed} for c in verdict.conditions],
        "reasons": verdict.reasons,
    }
    if verdict.expected_period is not None:
        result["expected_period"] = verdict.expected_period
    return result


def _jump(v: Mapping[str, Any]) -> dict[str, Any]:
    """Task: T068. Covers: FR-016, FR-017."""
    state = jump.jump(v["p"], v["state"], v["steps"])
    return {"state": state, "warnings": lcg.warnings_for(v["p"], v["state"])}


def _bounded(result: bounded.BoundedResult) -> dict[str, Any]:
    return {
        "values": result.values,
        "outputs_consumed": result.outputs_consumed,
        "next_state": result.next_state,
        "warnings": result.warnings,
    }


def _integers(v: Mapping[str, Any]) -> dict[str, Any]:
    """Task: T070. Covers: FR-019 to FR-021, FR-048."""
    return _bounded(bounded.integers(v["p"], v["seed"], v["lo"], v["hi"], v["count"]))


def _fractions(v: Mapping[str, Any]) -> dict[str, Any]:
    """Task: T070. Covers: FR-022."""
    return _bounded(bounded.fractions(v["p"], v["seed"], v["count"]))


def _quality(v: Mapping[str, Any]) -> dict[str, Any]:
    """Task: T075. Covers: FR-026 to FR-031."""
    r = quality.report(v["p"], v["seed"], v["sample_size"], v["bins"])
    return {
        "measured_period": r.measured_period,
        "chi_square": r.chi_square,
        "p_value": r.p_value,
        "serial_correlation": r.serial_correlation,
        "low_bit_periods": r.low_bit_periods,
        "checks": [{"name": c.name, "value": c.value, "outcome": c.outcome} for c in r.checks],
        "verdict": r.verdict,
        "notice": r.notice,
    }


def _streams(v: Mapping[str, Any]) -> dict[str, Any]:
    """Task: T084. Covers: FR-046, FR-047."""
    found = streams.split(v["p"], v["seed"], v["streams"], v["length"])
    return {
        "streams": [
            {"index": s.index, "start_state": s.start_state, "outputs": s.outputs} for s in found
        ],
        "warnings": lcg.warnings_for(v["p"], v["seed"]),
    }


HANDLERS: Mapping[str, Handler] = MappingProxyType(
    {
        "sequence": _sequence,
        "presets": _presets,
        "validate": _validate_handler,
        "jump": _jump,
        "integers": _integers,
        "fractions": _fractions,
        "quality": _quality,
        "streams": _streams,
    }
)
