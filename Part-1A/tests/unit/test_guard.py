"""Tests for lcgkit.core.guard.check_purpose (US6)."""

import pytest

from lcgkit.core.guard import check_purpose
from lcgkit.errors import LcgError

pytestmark = [pytest.mark.fr("FR-024")]

WORDS = ["token", "key", "password", "secret", "session", "nonce", "salt", "credential", "otp"]
PLURALS = [word + "s" for word in WORDS]


@pytest.mark.ac("AC-045")
@pytest.mark.parametrize("label", ["dice", "monkey business", "simulation", "", None])
def test_harmless_purposes_pass(label: str | None) -> None:
    assert check_purpose(label) is None


@pytest.mark.ac("AC-046")
@pytest.mark.parametrize("word", WORDS + PLURALS)
def test_every_listed_word_is_refused(word: str) -> None:
    for label in (word, word.upper(), word.title(), f"my {word} generator"):
        with pytest.raises(LcgError) as info:
            check_purpose(label)
        assert info.value.code == "insecure-purpose"


@pytest.mark.ac("AC-044")
@pytest.mark.parametrize("label", ["token", "Session Token", "KEYS", "api-key"])
def test_the_message_points_to_a_secure_source(label: str) -> None:
    with pytest.raises(LcgError) as info:
        check_purpose(label)
    assert info.value.code == "insecure-purpose"
    assert "cryptographically secure" in info.value.message
