"""The seven named generators."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from lcgkit.core.lcg import ParameterSet
from lcgkit.errors import LcgError


@dataclass(frozen=True)
class Preset:
    """A named parameter set with a one-line description."""

    name: str
    params: ParameterSet
    description: str


PRESETS: Mapping[str, Preset] = MappingProxyType(
    {
        p.name: p
        for p in (
            Preset("minstd", ParameterSet(16807, 0, 2**31 - 1), "Park-Miller minimal standard"),
            Preset(
                "minstd-new", ParameterSet(48271, 0, 2**31 - 1),
                "revised multiplier for the minimal standard",
            ),
            Preset(
                "glibc-type0", ParameterSet(1103515245, 12345, 2**31),
                "the simple mode of the GNU C library",
            ),
            Preset(
                "numrec", ParameterSet(1664525, 1013904223, 2**32),
                "Numerical Recipes' quick generator",
            ),
            Preset(
                "musl", ParameterSet(6364136223846793005, 1, 2**64),
                "the musl C library's rand",
            ),
            Preset(
                "pcg-lcg64", ParameterSet(6364136223846793005, 1442695040888963407, 2**64),
                "the 64-bit LCG used by the PCG family",
            ),
            Preset(
                "randu", ParameterSet(65539, 0, 2**31),
                "IBM's RANDU, included as a known-bad example",
            ),
        )
    }
)


def get(name: str) -> ParameterSet:
    """Return the parameters of the preset called `name`.

    Task: T062. Covers: FR-009, FR-012.
    """
    preset = PRESETS.get(name)
    if preset is None:
        raise LcgError("unknown-preset", f"there is no preset called {name!r}", "preset")
    return preset.params
