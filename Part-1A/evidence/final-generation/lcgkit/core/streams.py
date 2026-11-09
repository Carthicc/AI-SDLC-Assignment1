"""Split one sequence into separate streams that never overlap."""

from __future__ import annotations

from dataclasses import dataclass

from lcgkit.core.jump import jump
from lcgkit.core.lcg import ParameterSet, sequence


@dataclass(frozen=True)
class Stream:
    """A stream: its number, the state it starts from and its outputs."""

    index: int
    start_state: int
    outputs: list[int]


def split(p: ParameterSet, seed: int, streams: int, length: int) -> list[Stream]:
    """Return `streams` streams of `length` outputs; stream i starts at the state i * length
    steps after the seed, so joined in order they are the plain sequence.

    Task: T083. Covers: FR-046.
    """
    found = []
    for index in range(streams):
        start = jump(p, seed, index * length)
        found.append(Stream(index, start, sequence(p, start, length).outputs))
    return found
