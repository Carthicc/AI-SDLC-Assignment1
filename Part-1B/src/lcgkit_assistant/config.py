"""Named constants and the prompt file of lcgkit-assistant."""

from __future__ import annotations

import hashlib
from pathlib import Path

from lcgkit.fields import OPERATIONS as LCGKIT_OPERATIONS

MODEL = "gemini-3.5-flash-lite"
API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
KEY_VARIABLE = "GEMINI_API_KEY"
KEY_HEADER = "x-goog-api-key"
MAX_TEXT_LENGTH = 1000
MAX_FIELD_TEXT = 300
CALL_TIMEOUT_SECONDS = 60
RETRY_WAITS = (5, 15, 45)
RETRY_STATUSES = (429, 500, 502, 503, 504)
HTTP_OK = 200
TEMPERATURE = 0
RESPONSE_FORMAT = "application/json"
OPERATIONS = tuple(LCGKIT_OPERATIONS)
REFUSAL_REASONS = ("insecure-purpose", "out-of-scope", "unsafe-instruction")
EMPTY_TEXT_QUESTION = (
    "Please tell me what you would like to do with a linear congruential generator."
)
ERROR_CODES = (
    "request-too-long",
    "missing-api-key",
    "model-unavailable",
    "reply-not-json",
    "invalid-reply",
)
EXIT_OK = 0
EXIT_APPLICATION_ERROR = 2


def prompt_path() -> Path:
    """Return the path of the system prompt, `prompts/system.md` in the project root.

    Task: T041. Covers: FR-014.
    """
    return Path(__file__).resolve().parents[2] / "prompts" / "system.md"


def prompt_sha256() -> str:
    """Return the SHA-256 of the system prompt file, as hexadecimal text.

    Task: T041. Covers: FR-014, FR-015.
    """
    return hashlib.sha256(prompt_path().read_bytes()).hexdigest()
