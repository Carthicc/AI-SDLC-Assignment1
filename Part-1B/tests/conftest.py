"""Shared test support: marker checks, a fake model client, a fake transport and reply builders."""

from __future__ import annotations

import re
from typing import Any

import pytest

MARKER = "lcgkit-assistant-marker-7f3a9c"
MARKER_FORMS = {
    "ac": re.compile(r"AC-\d{3}"),
    "fr": re.compile(r"FR-\d{3}"),
    "inv": re.compile(r"INV-\d{2}"),
    "prop": re.compile(r"PROP-\d{2}"),
}


def pytest_configure(config: pytest.Config) -> None:
    """Register the traceability markers."""
    for name in MARKER_FORMS:
        config.addinivalue_line("markers", f"{name}(id): traceability marker")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Fail the collection if a marker is not AC-nnn, FR-nnn, INV-nn or PROP-nn."""
    for item in items:
        for name, form in MARKER_FORMS.items():
            for marker in item.iter_markers(name):
                if len(marker.args) != 1 or not form.fullmatch(str(marker.args[0])):
                    raise pytest.UsageError(f"{item.nodeid}: bad {name} marker {marker.args!r}")


class FakeClient:
    """Stands in for the Gemini client: records the texts and returns or raises queued values."""

    def __init__(self, *queued: Any) -> None:
        self.queue = list(queued)
        self.texts: list[str] = []

    def generate(self, text: str) -> Any:
        """Return the next queued result, or raise it if it is an exception."""
        self.texts.append(text)
        item = self.queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def fake_transport(responses: list[Any]) -> Any:
    """A transport that returns queued (status, headers, body) tuples, or raises queued exceptions.

    The returned function has a `calls` list holding (url, headers, body, timeout) for each request.
    """
    queue = list(responses)

    def transport(
        url: str, headers: dict[str, str], body: bytes, timeout: int
    ) -> tuple[int, dict, bytes]:
        transport.calls.append((url, headers, body, timeout))
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    transport.calls = []
    return transport


def call_reply(operation: str = "sequence", **arguments: Any) -> dict[str, Any]:
    """A valid `call` reply (a minstd sequence unless told otherwise)."""
    if not arguments and operation == "sequence":
        arguments = {"preset": "minstd", "seed": "42", "count": 5}
    return {"decision": "call", "operation": operation, "arguments": arguments}


def clarify_reply(
    question: str = "Which seed should I use?", missing: list[str] | None = None
) -> dict[str, Any]:
    """A valid `clarify` reply."""
    return {
        "decision": "clarify",
        "question": question,
        "missing": ["seed"] if missing is None else missing,
    }


def refuse_reply(
    reason: str = "insecure-purpose", message: str = "Not suitable for that purpose."
) -> dict[str, Any]:
    """A valid `refuse` reply."""
    return {"decision": "refuse", "reason": reason, "message": message}
