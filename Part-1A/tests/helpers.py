"""Small helpers shared by the test files."""

from __future__ import annotations

from collections.abc import Mapping

import pytest
from lcgkit.errors import LcgError
from lcgkit.ops import run

GLIBC = {"a": 1103515245, "c": 12345, "m": 2**31}


def error_of(operation: str, request: Mapping[str, object]) -> LcgError:
    """Run an operation that must fail and return the error it raised."""
    with pytest.raises(LcgError) as info:
        run(operation, request)
    return info.value
