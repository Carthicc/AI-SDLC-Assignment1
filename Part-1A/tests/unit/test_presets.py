"""Tests for lcgkit.core.presets and the published values of the seven presets (US2)."""

import pytest

from lcgkit.core import presets
from lcgkit.core.lcg import sequence
from tests.conftest import PRESET_TABLE
from tests.oracle import reference as ref

pytestmark = [pytest.mark.fr("FR-009")]

# (preset, seed, first outputs) from AC-013 to AC-019.
PUBLISHED = [
    pytest.param("minstd", 1, [16807, 282475249, 1622650073, 984943658, 1144108930],
                 marks=pytest.mark.ac("AC-013")),
    pytest.param("minstd-new", 1, [48271, 182605794, 1291394886], marks=pytest.mark.ac("AC-014")),
    pytest.param("glibc-type0", 1, [1103527590, 377401575, 662824084],
                 marks=pytest.mark.ac("AC-015")),
    pytest.param("numrec", 0, [1013904223, 1196435762, 3519870697],
                 marks=pytest.mark.ac("AC-016")),
    pytest.param("musl", 0, [1, 6364136223846793006, 13885033948157127959],
                 marks=pytest.mark.ac("AC-017")),
    pytest.param("pcg-lcg64", 0, [1442695040888963407, 1876011003808476466],
                 marks=pytest.mark.ac("AC-018")),
    pytest.param("randu", 1, [65539, 393225, 1769499, 7077969], marks=pytest.mark.ac("AC-019")),
]


def test_the_seven_presets_are_registered_in_order() -> None:
    assert list(presets.PRESETS) == list(PRESET_TABLE)


@pytest.mark.parametrize("name", list(PRESET_TABLE))
def test_parameters_match_the_specification(name: str) -> None:
    p = presets.get(name)
    assert (p.a, p.c, p.m) == tuple(PRESET_TABLE[name].values())


@pytest.mark.parametrize(("name", "seed", "expected"), PUBLISHED)
def test_first_outputs_match_the_published_values(
    name: str, seed: int, expected: list[int]
) -> None:
    result = sequence(presets.get(name), seed, len(expected))
    assert list(result.outputs) == expected


@pytest.mark.ac("AC-013")
def test_minstd_ten_thousandth_output() -> None:
    result = sequence(presets.get("minstd"), 1, 10_000)
    assert result.outputs[-1] == ref.MINSTD_10000TH == 1043618065


@pytest.mark.ac("AC-014")
def test_minstd_new_ten_thousandth_output() -> None:
    result = sequence(presets.get("minstd-new"), 1, 10_000)
    assert result.outputs[-1] == ref.MINSTD_NEW_10000TH == 399268537
