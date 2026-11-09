"""The purpose guard: refuses declared purposes that need a secure random source."""

from __future__ import annotations

import re

from lcgkit.errors import LcgError

INSECURE_WORDS = frozenset(
    {"token", "key", "password", "secret", "session", "nonce", "salt", "credential", "otp"}
)
WORD = re.compile(r"[^\W_]+")
PLURAL_ENDING = "s"
MESSAGE = (
    "A linear congruential generator is not suitable for {label!r}: its output can be predicted. "
    "Use a cryptographically secure source, such as the operating system's secure random "
    "generator."
)


def _is_insecure(word: str) -> bool:
    """True for a listed word or its plural."""
    return word in INSECURE_WORDS or (
        word.endswith(PLURAL_ENDING) and word[: -len(PLURAL_ENDING)] in INSECURE_WORDS
    )


def check_purpose(label: str | None) -> None:
    """Raise `insecure-purpose` if any whole word of the label names a security use.

    Task: T071. Covers: FR-023, FR-024.
    """
    if not label:
        return
    if any(_is_insecure(word) for word in WORD.findall(label.strip().lower())):
        raise LcgError("insecure-purpose", MESSAGE.format(label=label), "purpose")
