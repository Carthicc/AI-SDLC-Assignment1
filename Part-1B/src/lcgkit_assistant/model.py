"""The call to the Gemini service: request, retries and parsing (FR-014, FR-015)."""

from __future__ import annotations

import http.client
import json
import time
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from lcgkit.fields import COUNT, FIELDS, LARGE_LIST

from lcgkit_assistant import config

Transport = Callable[[str, dict[str, str], bytes, int], tuple[int, dict[str, str], bytes]]
FORBIDDEN_ARGUMENT = "purpose"


@dataclass(frozen=True)
class ModelResult:
    """The text of the model's reply (None if it had none) and the requests made."""

    text: str | None
    calls: int


class ModelUnavailable(Exception):
    """The model service could not give a reply; `calls` is the number of requests made."""

    def __init__(self, message: str, calls: int) -> None:
        """Create the error; the message never contains the key.

        Task: T043. Covers: FR-014, FR-015.
        """
        super().__init__(message)
        self.calls = calls


def _argument_type(name: str) -> dict[str, Any]:
    kind = FIELDS[name].kind
    if kind == COUNT:
        return {"type": "INTEGER"}
    if kind == LARGE_LIST:
        return {"type": "ARRAY", "items": {"type": "STRING"}}
    return {"type": "STRING"}


def reply_schema() -> dict[str, Any]:
    """The flat response schema that guides the model; the code still checks every reply."""
    arguments = {name: _argument_type(name) for name in FIELDS if name != FORBIDDEN_ARGUMENT}
    return {
        "type": "OBJECT",
        "properties": {
            "decision": {"type": "STRING", "enum": ["call", "clarify", "refuse"]},
            "operation": {"type": "STRING", "enum": list(config.OPERATIONS)},
            "arguments": {"type": "OBJECT", "properties": arguments},
            "question": {"type": "STRING"},
            "missing": {"type": "ARRAY", "items": {"type": "STRING"}},
            "reason": {"type": "STRING", "enum": list(config.REFUSAL_REASONS)},
            "message": {"type": "STRING"},
        },
        "required": ["decision"],
    }


def _https_transport(
    url: str, headers: dict[str, str], body: bytes, timeout: int
) -> tuple[int, dict[str, str], bytes]:
    parts = urllib.parse.urlsplit(url)
    connection = http.client.HTTPSConnection(parts.netloc, timeout=timeout)
    try:
        connection.request("POST", parts.path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def _retry_after(headers: dict[str, str]) -> int | None:
    value = {name.lower(): text for name, text in headers.items()}.get("retry-after", "")
    return int(value) if value.isdigit() else None


def _reply_text(data: bytes) -> str | None:
    try:
        return json.loads(data)["candidates"][0]["content"]["parts"][0]["text"]
    except (ValueError, KeyError, IndexError, TypeError):
        return None


class GeminiClient:
    """Sends one request text to Gemini and returns the text of the reply."""

    def __init__(
        self,
        api_key: str,
        transport: Transport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a client; `transport` and `sleep` are replaced in tests.

        Task: T043. Covers: FR-014, FR-015.
        """
        self._api_key = api_key
        self._transport = transport or _https_transport
        self._sleep = sleep

    def _payload(self, text: str) -> bytes:
        body = {
            "systemInstruction": {"parts": [{"text": config.prompt_path().read_text()}]},
            "contents": [{"role": "user", "parts": [{"text": text}]}],
            "generationConfig": {
                "temperature": config.TEMPERATURE,
                "responseMimeType": config.RESPONSE_FORMAT,
                "responseSchema": reply_schema(),
            },
        }
        return json.dumps(body).encode()

    def _send(self, body: bytes) -> tuple[int | None, dict[str, str], bytes]:
        """One request; a timeout or connection error gives the status None."""
        url = config.API_URL_TEMPLATE.format(model=config.MODEL)
        headers = {"Content-Type": "application/json", config.KEY_HEADER: self._api_key}
        try:
            return self._transport(url, headers, body, config.CALL_TIMEOUT_SECONDS)
        except (OSError, http.client.HTTPException):
            return None, {}, b""

    def generate(self, text: str) -> ModelResult:
        """Ask the model about `text`, retrying rate limits, server errors and timeouts.

        Task: T043. Covers: FR-014, FR-015, AC-047, AC-054.
        """
        body = self._payload(text)
        calls = 0
        for wait in (*config.RETRY_WAITS, None):
            calls += 1
            status, headers, data = self._send(body)
            if status == config.HTTP_OK:
                return ModelResult(_reply_text(data), calls)
            if status is not None and status not in config.RETRY_STATUSES:
                raise ModelUnavailable(f"the model service answered status {status}", calls)
            if wait is not None:
                self._sleep(_retry_after(headers) or wait)
        raise ModelUnavailable("the model service stayed unavailable after the retries", calls)
