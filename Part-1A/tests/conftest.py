"""Shared test setup: markers, the preset table, the Hypothesis profile and `canonical`."""

from __future__ import annotations

import json
import re

import pytest
from hypothesis import settings

# The seven presets exactly as written in AC-013 to AC-019, in the order of AC-020.
# Kept here as plain numbers so expected values never come from src/.
PRESET_TABLE: dict[str, dict[str, int]] = {
    "minstd": {"a": 16807, "c": 0, "m": 2**31 - 1},
    "minstd-new": {"a": 48271, "c": 0, "m": 2**31 - 1},
    "glibc-type0": {"a": 1103515245, "c": 12345, "m": 2**31},
    "numrec": {"a": 1664525, "c": 1013904223, "m": 2**32},
    "musl": {"a": 6364136223846793005, "c": 1, "m": 2**64},
    "pcg-lcg64": {"a": 6364136223846793005, "c": 1442695040888963407, "m": 2**64},
    "randu": {"a": 65539, "c": 0, "m": 2**31},
}

MARKER_FORMS = {"ac": re.compile(r"AC-\d{3}"), "fr": re.compile(r"FR-\d{3}")}

settings.register_profile("lcgkit", derandomize=True, max_examples=100, deadline=None)
settings.load_profile("lcgkit")


def pytest_configure(config: pytest.Config) -> None:
    """Register the markers used to trace tests back to the specification."""
    config.addinivalue_line("markers", "ac(id): acceptance criterion the test checks, AC-nnn")
    config.addinivalue_line("markers", "fr(id): functional requirement the test checks, FR-nnn")
    config.addinivalue_line("markers", "perf: timing test with a time limit")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Stop the run if an ac or fr marker is not of the form AC-nnn or FR-nnn."""
    for item in items:
        for name, form in MARKER_FORMS.items():
            for marker in item.iter_markers(name=name):
                if len(marker.args) != 1 or not form.fullmatch(str(marker.args[0])):
                    raise pytest.UsageError(
                        f"{item.nodeid}: marker {name}{marker.args} must be one {form.pattern} ID"
                    )


def canonical(obj: object) -> bytes:
    """Return a byte string for `obj` that is the same whenever the content is the same."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()
