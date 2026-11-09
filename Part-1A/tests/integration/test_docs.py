"""The documentation states the limit of the purpose guard (US6)."""

from pathlib import Path

import pytest

pytestmark = [pytest.mark.ac("AC-048"), pytest.mark.fr("FR-025")]

README = Path(__file__).resolve().parents[2] / "README.md"
SENTENCE = (
    "The purpose guard relies on the declared purpose and cannot catch misuse that is not declared."
)


def test_readme_states_the_limit_of_the_guard() -> None:
    assert SENTENCE in README.read_text()
