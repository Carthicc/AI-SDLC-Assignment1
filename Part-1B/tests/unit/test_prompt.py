"""The system prompt: required content, and nothing copied from the evaluation dataset."""

import hashlib
import json
from pathlib import Path

import pytest

from lcgkit_assistant import config

ROOT = Path(__file__).parents[2]
PROMPT = ROOT / "prompts" / "system.md"
OPERATIONS = (
    "presets",
    "sequence",
    "integers",
    "fractions",
    "jump",
    "streams",
    "validate",
    "quality",
    "predict",
)
REASONS = ("insecure-purpose", "out-of-scope", "unsafe-instruction")


@pytest.fixture(name="text")
def text_fixture():
    return PROMPT.read_text()


@pytest.mark.fr("FR-014")
@pytest.mark.prop("PROP-06")
def test_the_marker_phrase_matches_the_declared_one(text):
    declared = json.loads((ROOT / ".harness" / "threshold.json").read_text())["marker_phrase"]
    assert declared in text


@pytest.mark.fr("FR-014")
def test_it_names_the_operations_the_limit_and_the_reasons(text):
    for word in (*OPERATIONS, *REASONS, "1,000,000"):
        assert word in text, word


@pytest.mark.fr("FR-015")
def test_it_holds_no_text_from_the_dataset(text):
    cases = json.loads((ROOT / "evals" / "dataset.json").read_text())["cases"]
    copied = [case["id"] for case in cases if case["text"].strip() and case["text"] in text]
    assert copied == []


@pytest.mark.fr("FR-015")
def test_the_hash_is_the_hash_of_the_file():
    assert config.prompt_sha256() == hashlib.sha256(PROMPT.read_bytes()).hexdigest()
