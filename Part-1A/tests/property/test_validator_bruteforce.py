"""The validator against brute force for every small generator (US3)."""

import pytest

from lcgkit.core.lcg import ParameterSet
from lcgkit.core.validator import validate
from tests.oracle.reference import full_period_by_brute_force

pytestmark = [pytest.mark.ac("AC-027"), pytest.mark.fr("FR-015")]

SMALLEST = 2
LARGEST = 64


def test_the_sweep_covers_89439_triples() -> None:
    assert sum(m * m for m in range(SMALLEST, LARGEST + 1)) == 89_439


@pytest.mark.parametrize("m", range(SMALLEST, LARGEST + 1))
def test_verdict_equals_brute_force(m: int) -> None:
    disagreements = [
        (a, c)
        for a in range(m)
        for c in range(m)
        if (validate(ParameterSet(a, c, m)).verdict == "full-period")
        != full_period_by_brute_force(a, c, m)
    ]
    assert disagreements == []
