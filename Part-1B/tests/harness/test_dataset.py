"""The dataset loader and checker, and the real dataset."""

import copy
import json
from pathlib import Path

import dataset
import pytest

ROOT = Path(__file__).parents[2]
SPEC = ROOT / "specs" / "001-lcgkit-assistant" / "spec.md"
DATASET = ROOT / "evals" / "dataset.json"


@pytest.fixture(name="data")
def data_fixture():
    return dataset.load(DATASET)


@pytest.mark.ac("AC-048")
@pytest.mark.fr("FR-028")
def test_the_real_dataset_has_no_problems(data):
    assert dataset.validate(data, SPEC) == []


@pytest.mark.fr("FR-020")
def test_the_real_dataset_shape(data):
    cases = data["cases"]
    assert [c["id"] for c in cases] == [f"C{i:02d}" for i in range(1, 49)]
    for operation in dataset.OPERATIONS:
        wanted = [c for c in cases if c["expected"].get("operation") == operation]
        assert len(wanted) >= 2, operation
    assert {c["category"] for c in cases} == set(dataset.CATEGORIES)
    assert sum(c["guardrail"] for c in cases) >= 6
    near = [c for c in cases if c["guardrail"] and "PROP-05" in c["covers"]]
    assert len(near) >= 2


@pytest.mark.fr("FR-020")
def test_texts_are_short_and_hold_no_key(data):
    for case in data["cases"]:
        assert len(case["text"]) <= 1200
        assert "AIza" not in case["text"]
        assert "AQ." not in case["text"]


def broken(data, change):
    other = copy.deepcopy(data)
    change(other)
    return dataset.validate(other, SPEC)


def drop_text(d):
    del d["cases"][0]["text"]


def drop_presets_case(d):
    d["cases"] = [c for c in d["cases"] if c["id"] != "C14"]


def drop_cover(d):
    d["cases"][8]["covers"].remove("AC-009")


@pytest.mark.ac("AC-048")
@pytest.mark.parametrize(
    ("change", "expected_text"),
    [
        (lambda d: d.update(cases=d["cases"][:10]), "at least 30"),
        (lambda d: d["cases"].append(copy.deepcopy(d["cases"][0])), "duplicate case id C01"),
        (drop_text, "missing field text"),
        (drop_presets_case, "operation presets has 1 call cases"),
        (lambda d: d["cases"][0]["covers"].append("AC-999"), "unknown id AC-999"),
        (drop_cover, "AC-009 has no case"),
        (
            lambda d: d["covered_elsewhere"].update({"AC-001": "x"}),
            "AC-001 is covered by a case and listed",
        ),
    ],
)
def test_broken_datasets_are_rejected(data, change, expected_text):
    problems = broken(data, change)
    assert any(expected_text in problem for problem in problems), problems


@pytest.mark.fr("FR-028")
def test_spec_ids_are_found():
    ids = dataset.spec_ids(SPEC)
    assert {"AC-001", "INV-06", "PROP-09"} <= ids
    assert len(ids) == 76


def test_loading_a_non_object_fails(tmp_path):
    path = tmp_path / "d.json"
    path.write_text(json.dumps([1]))
    with pytest.raises(ValueError, match="JSON object"):
        dataset.load(path)
