"""Tests for lcgkit.core.numtheory: primality and factoring (cites FR-014)."""

import time

import pytest
from lcgkit.core.numtheory import factor, is_prime

from tests.oracle.reference import trial_factor

pytestmark = [pytest.mark.fr("FR-014")]

# Composite numbers that fool weak primality tests.
PSEUDOPRIMES = [2047, 3215031751, 3825123056546413051]
CARMICHAEL = [561, 1105]
LARGE_PRIME_PAIR = (4294967291, 4294967279)  # two primes just below 2**32


def test_is_prime_agrees_with_trial_division_below_100000() -> None:
    wrong = [n for n in range(100_000) if is_prime(n) != (n > 1 and trial_factor(n) == {n: 1})]
    assert wrong == []


@pytest.mark.parametrize("n", PSEUDOPRIMES + CARMICHAEL)
def test_is_prime_rejects_pseudoprimes(n: int) -> None:
    assert not is_prime(n)


@pytest.mark.parametrize("n", [2**31 - 1, 2**61 - 1, *LARGE_PRIME_PAIR])
def test_is_prime_accepts_known_primes(n: int) -> None:
    assert is_prime(n)


def test_factor_agrees_with_trial_division() -> None:
    values = [(i * 4_999_999_937 + i**3 * 1_000_003) % (10**12 - 2) + 2 for i in range(1, 201)]
    assert [factor(n) for n in values] == [trial_factor(n) for n in values]


def test_factor_of_a_power_of_two() -> None:
    assert factor(2**64) == {2: 64}


def test_factor_of_a_product_of_two_32_bit_primes() -> None:
    n = LARGE_PRIME_PAIR[0] * LARGE_PRIME_PAIR[1]
    started = time.perf_counter()
    assert factor(n) == {LARGE_PRIME_PAIR[0]: 1, LARGE_PRIME_PAIR[1]: 1}
    assert time.perf_counter() - started < 1
