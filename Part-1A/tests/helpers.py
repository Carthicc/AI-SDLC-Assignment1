"""Small helpers and the shared example set used by several test files."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from lcgkit.errors import LcgError
from lcgkit.ops import run
from tests.oracle.reference import step_sequence

GLIBC = {"a": 1103515245, "c": 12345, "m": 2**31}
# Fields that can exceed 2**53 travel as decimal strings in JSON (FR-033).
LARGE_FIELDS = {"a", "c", "m", "seed", "state", "steps", "lo", "hi"}
GLIBC_FROM_ONE = step_sequence(GLIBC["a"], GLIBC["c"], GLIBC["m"], 1, 20)
HIDDEN_BITS = 16

# One request per interesting case, covering every operation: (operation, request).
EXAMPLES: list[tuple[str, dict[str, object]]] = [
    ("presets", {}),
    ("sequence", {"a": 5, "c": 3, "m": 16, "seed": 7, "count": 5}),
    ("sequence", {"preset": "pcg-lcg64", "seed": 0, "count": 3}),
    ("integers", {"a": 5, "c": 3, "m": 16, "seed": 7, "lo": 1, "hi": 3, "count": 15}),
    ("integers", {"preset": "glibc-type0", "seed": 1, "lo": -3, "hi": 3, "count": 20}),
    ("fractions", {"a": 5, "c": 3, "m": 16, "seed": 7, "count": 5}),
    ("jump", {"preset": "minstd", "state": 1, "steps": 10_000}),
    ("streams", {"preset": "glibc-type0", "seed": 1, "streams": 4, "length": 5}),
    ("validate", {"preset": "minstd"}),
    ("validate", {"a": 5, "c": 3, "m": 16}),
    ("quality", {"preset": "minstd", "seed": 1, "sample_size": 1000, "bins": 10}),
    ("quality", {"a": 5, "c": 3, "m": 16, "seed": 7, "sample_size": 16, "bins": 16}),
    ("predict", {"m": 2**31, "outputs": GLIBC_FROM_ONE[:5]}),
    ("predict", {"outputs": GLIBC_FROM_ONE[:12]}),
    ("predict", {**GLIBC, "hidden_bits": HIDDEN_BITS,
                 "outputs": [x >> HIDDEN_BITS for x in GLIBC_FROM_ONE[:4]]}),
]


def error_of(operation: str, request: Mapping[str, object]) -> LcgError:
    """Run an operation that must fail and return the error it raised."""
    with pytest.raises(LcgError) as info:
        run(operation, request)
    return info.value


def http_body(request: Mapping[str, object]) -> dict[str, object]:
    """Write a request the way the JSON interfaces expect: large integers as strings."""
    body: dict[str, object] = {}
    for name, value in request.items():
        if name in LARGE_FIELDS:
            body[name] = str(value)
        elif name == "outputs" and isinstance(value, list):
            body[name] = [str(item) for item in value]
        else:
            body[name] = value
    return body


def cli_args(request: Mapping[str, object]) -> list[str]:
    """Write a request as command-line options (field names with hyphens)."""
    args = []
    for name, value in request.items():
        text = ",".join(str(item) for item in value) if isinstance(value, list) else str(value)
        args.append(f"--{name.replace('_', '-')}={text}")
    return args


def leaves(value: object) -> list[object]:
    """Every integer (not boolean) and string inside a result."""
    if isinstance(value, dict):
        return [leaf for item in value.values() for leaf in leaves(item)]
    if isinstance(value, list | tuple):
        return [leaf for item in value for leaf in leaves(item)]
    if isinstance(value, bool) or not isinstance(value, int | str):
        return []
    return [value]
