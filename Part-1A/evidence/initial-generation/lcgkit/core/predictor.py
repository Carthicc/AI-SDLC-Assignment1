"""Predict a generator's next outputs from what has been seen, to show it is not secure."""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from lcgkit.core.lcg import ParameterSet, sequence
from lcgkit.core.numtheory import solve_linear
from lcgkit.errors import LcgError

NOTICE = "This prediction shows that the generator is not secure."
CASE_B_ADDITION = " Recovering the modulus is probable, not certain."
MIN_OUTPUTS_KNOWN_MODULUS = 3
MIN_OUTPUTS_UNKNOWN_MODULUS = 12
MAX_HIDDEN_BITS = 20
MAX_CANDIDATES = 1 << 16
AMBIGUOUS = 2


@dataclass(frozen=True)
class Prediction:
    """A recovered generator (or state) and the values predicted from it."""

    case: str
    modulus: int | None
    a: int | None
    c: int | None
    state: int | None
    predictions: list[int]
    notice: str


def _reproduces(outputs: list[int], a: int, c: int, m: int) -> bool:
    """True if a and c generate every supplied output from the one before."""
    return all(outputs[i + 1] == (a * outputs[i] + c) % m for i in range(len(outputs) - 1))


def predict_known_modulus(m: int, outputs: list[int], k: int) -> Prediction:
    """Case A: recover a and c from at least three outputs when the modulus is known.

    Task: T081. Covers: FR-039, FR-042, FR-043.
    """
    if len(outputs) < MIN_OUTPUTS_KNOWN_MODULUS:
        raise LcgError("insufficient-data", "at least 3 outputs are needed", "outputs")
    x1, x2, x3 = outputs[:MIN_OUTPUTS_KNOWN_MODULUS]
    first, second = (x2 - x1) % m, (x3 - x2) % m
    if gcd(first, m) > MAX_CANDIDATES:
        raise LcgError("ambiguous-parameters", "too many multipliers fit these outputs")
    fits = []
    for a in solve_linear(first, second, m):
        c = (x2 - a * x1) % m
        if _reproduces(outputs, a, c, m):
            fits.append((a, c))
    if not fits:
        raise LcgError("insufficient-data", "no multiplier and increment fit these outputs")
    if len(fits) > 1:
        raise LcgError("ambiguous-parameters", "several multipliers fit these outputs equally")
    a, c = fits[0]
    predictions = sequence(ParameterSet(a, c, m), outputs[-1], k).outputs
    return Prediction("A", None, a, c, None, predictions, NOTICE)


def predict_unknown_modulus(outputs: list[int], k: int) -> Prediction:
    """Case B: recover the modulus from at least 12 outputs, then proceed as case A.

    Task: T081. Covers: FR-040, FR-042, FR-043.
    """
    if len(outputs) < MIN_OUTPUTS_UNKNOWN_MODULUS:
        raise LcgError("insufficient-data", "at least 12 outputs are needed", "outputs")
    t = [outputs[i + 1] - outputs[i] for i in range(len(outputs) - 1)]
    g = 0
    for i in range(len(t) - 2):
        g = gcd(g, abs(t[i + 2] * t[i] - t[i + 1] ** 2))
    if g <= max(outputs):
        raise LcgError("insufficient-data", "the modulus cannot be recovered from these outputs")
    found = predict_known_modulus(g, outputs, k)
    return Prediction("B", g, found.a, found.c, None, found.predictions, NOTICE + CASE_B_ADDITION)


def _matching_states(p: ParameterSet, hidden: int, outputs: list[int]) -> list[int]:
    """States whose high bits give the first output and whose next steps give the others.

    Stops once two are found, since that already makes the answer ambiguous.
    """
    a, c, m = p.a, p.c, p.m
    found: list[int] = []
    for low in range(1 << hidden):
        x = (outputs[0] << hidden) | low
        if x >= m:
            break
        state = x
        for seen in outputs[1:]:
            state = (a * state + c) % m
            if state >> hidden != seen:
                break
        else:
            found.append(x)
            if len(found) == AMBIGUOUS:
                break
    return found


def predict_truncated(p: ParameterSet, hidden_bits: int, outputs: list[int], k: int) -> Prediction:
    """Case C: recover the internal state from outputs that lost their low `hidden_bits` bits.

    Task: T081. Covers: FR-041, FR-042, FR-043.
    """
    if p.m & (p.m - 1) != 0 or hidden_bits > MAX_HIDDEN_BITS:
        raise LcgError(
            "unsupported-combination",
            f"needs a power-of-two modulus and at most {MAX_HIDDEN_BITS} hidden bits",
            "hidden_bits",
        )
    states = _matching_states(p, hidden_bits, outputs)
    if not states:
        raise LcgError("insufficient-data", "no state fits these outputs")
    if len(states) > 1:
        raise LcgError("ambiguous-parameters", "several states fit these outputs equally")
    state = sequence(p, states[0], len(outputs) - 1).next_state
    predictions = sequence(p, state, k).outputs
    return Prediction("C", None, None, None, state, predictions, NOTICE)
