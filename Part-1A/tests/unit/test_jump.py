"""Tests for lcgkit.core.jump: jump-ahead by doubling the map (US4)."""

import pytest

from lcgkit.core import jump as jump_module
from lcgkit.core import presets
from lcgkit.core.jump import jump
from tests.conftest import PRESET_TABLE
from tests.oracle import reference as ref

pytestmark = [pytest.mark.fr("FR-016"), pytest.mark.fr("FR-018")]

GLIBC = presets.get("glibc-type0")
MAX_MULTIPLICATIONS = 192


@pytest.mark.ac("AC-029")
@pytest.mark.parametrize("name", list(PRESET_TABLE))
def test_jump_equals_stepping_for_every_distance_to_1000(name: str) -> None:
    t = PRESET_TABLE[name]
    p = presets.get(name)
    walked = [1, *ref.step_sequence(t["a"], t["c"], t["m"], 1, 1000)]
    assert [jump(p, 1, n) for n in range(1001)] == walked


@pytest.mark.ac("AC-030")
def test_minstd_ten_thousand_steps() -> None:
    assert jump(presets.get("minstd"), 1, 10_000) == 1043618065


@pytest.mark.ac("AC-031")
@pytest.mark.parametrize("seed", [0, 1, 12345, 2**31 - 1])
def test_a_full_period_brings_the_state_back(seed: int) -> None:
    assert jump(GLIBC, seed, 2**31) == seed
    assert jump(GLIBC, seed, 2**31 + 5) == jump(GLIBC, seed, 5)
    assert jump(GLIBC, seed, 5) == ref.step_sequence(GLIBC.a, GLIBC.c, GLIBC.m, seed, 5)[-1]


@pytest.mark.ac("AC-032")
@pytest.mark.parametrize(
    ("first", "second"), [(0, 7), (1, 1), (1000, 2345), (2**40 + 1, 2**33), (2**63, 2**63 - 1)]
)
def test_two_jumps_equal_one(first: int, second: int) -> None:
    p = presets.get("pcg-lcg64")
    halfway = jump(p, 99, first)
    assert jump(p, halfway, second) == jump(p, 99, first + second)


@pytest.mark.ac("AC-034")
@pytest.mark.parametrize("steps", [2**64 - 1, 2**63, 12345, 1, 0])
def test_at_most_192_modular_multiplications(
    steps: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []
    original = jump_module.mulmod

    def counting(*args: int) -> int:
        calls.append(args)
        return original(*args)

    monkeypatch.setattr(jump_module, "mulmod", counting)
    p = presets.get("pcg-lcg64")
    state = jump(p, 5, steps)
    assert len(calls) <= MAX_MULTIPLICATIONS
    assert state == ref.closed_form_state(p.a, p.c, p.m, 5, steps)
