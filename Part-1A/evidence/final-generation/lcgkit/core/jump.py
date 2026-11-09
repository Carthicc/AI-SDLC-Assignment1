"""Jump ahead n steps by doubling the affine map x -> A*x + C."""

from __future__ import annotations

from lcgkit.core.lcg import ParameterSet


def mulmod(x: int, y: int, m: int) -> int:
    """Return x * y modulo m; the only place a modular multiplication is done.

    Task: T067. Covers: FR-018.
    """
    return x * y % m


def jump(p: ParameterSet, state: int, steps: int) -> int:
    """Return the state `steps` steps after `state`, using at most three mulmod per bit.

    The map for 2**i steps is x -> A*x + C; it is applied when bit i of `steps` is set and
    then doubled, so no loop runs in proportion to `steps`.

    Task: T067. Covers: FR-016, FR-018.
    """
    m = p.m
    mult, add = p.a, p.c
    while steps:
        if steps & 1:
            state = (mulmod(mult, state, m) + add) % m
        steps >>= 1
        if steps:
            add = mulmod(add, mult + 1, m)
            mult = mulmod(mult, mult, m)
    return state
