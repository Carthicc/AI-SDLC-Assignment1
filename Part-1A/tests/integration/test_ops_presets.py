"""Tests for the presets operation and naming a preset in a request (US2)."""

import pytest
from lcgkit.ops import run

from tests.conftest import PRESET_TABLE, canonical
from tests.helpers import error_of

pytestmark = [pytest.mark.fr("FR-010"), pytest.mark.fr("FR-011"), pytest.mark.fr("FR-012")]


@pytest.mark.ac("AC-020")
def test_list_of_presets() -> None:
    listed = run("presets", {})["presets"]
    assert [item["name"] for item in listed] == list(PRESET_TABLE)
    for item in listed:
        expected = PRESET_TABLE[item["name"]]
        assert (item["a"], item["c"], item["m"]) == (expected["a"], expected["c"], expected["m"])
        assert item["description"].strip()
        assert "\n" not in item["description"]


@pytest.mark.ac("AC-021")
@pytest.mark.parametrize("name", list(PRESET_TABLE))
def test_a_preset_equals_its_parameters_written_out(name: str) -> None:
    by_name = run("sequence", {"preset": name, "seed": 1, "count": 5})
    written = run("sequence", {**PRESET_TABLE[name], "seed": 1, "count": 5})
    assert canonical(by_name) == canonical(written)


@pytest.mark.ac("AC-022")
def test_unknown_preset() -> None:
    error = error_of("sequence", {"preset": "nope", "seed": 1, "count": 5})
    assert (error.code, error.field) == ("unknown-preset", "preset")
