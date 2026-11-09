"""Primality and factoring for integers up to 2**64, without randomness."""

from __future__ import annotations

from math import gcd, isqrt

# The first twelve primes: as Miller-Rabin bases they decide primality for n < 3.3 * 10**24.
SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
TRIAL_LIMIT = 1000
SMALLEST_PRIME = 2


def _is_witness(base: int, odd: int, twos: int, n: int) -> bool:
    """True if `base` proves n composite (one Miller-Rabin round)."""
    x = pow(base, odd, n)
    if x in (1, n - 1):
        return False
    for _ in range(twos - 1):
        x = x * x % n
        if x == n - 1:
            return False
    return True


def is_prime(n: int) -> bool:
    """Deterministic primality test.

    Task: T064. Covers: FR-014.
    """
    if n < SMALLEST_PRIME:
        return False
    for p in SMALL_PRIMES:
        if n % p == 0:
            return n == p
    odd, twos = n - 1, 0
    while odd % 2 == 0:
        odd //= 2
        twos += 1
    return not any(_is_witness(base, odd, twos, n) for base in SMALL_PRIMES)


def _rho(n: int, c: int) -> int:
    """Pollard-Brent: a divisor of n found with f(x) = x*x + c, possibly n itself."""
    x = y = 2
    run, g = 1, 1
    while g == 1:
        x = y
        for _ in range(run):
            y = (y * y + c) % n
        for _ in range(run):
            y = (y * y + c) % n
            g = gcd(abs(x - y), n)
            if g != 1:
                break
        run *= 2
    return g


def _find_divisor(n: int) -> int:
    """A proper divisor of the composite n, trying c = 1, 2, 3, ... in a fixed order."""
    root = isqrt(n)
    if root * root == n:
        return root
    c = 1
    while True:
        g = _rho(n, c)
        if 1 < g < n:
            return g
        c += 1


def _strip_small(n: int, factors: dict[int, int]) -> int:
    """Divide out every prime below TRIAL_LIMIT, recording it; return what is left."""
    for d in range(2, TRIAL_LIMIT):
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
    return n


def _split(n: int, factors: dict[int, int]) -> None:
    """Add the prime factorisation of n (all factors above TRIAL_LIMIT) to `factors`."""
    if n == 1:
        return
    if is_prime(n):
        factors[n] = factors.get(n, 0) + 1
        return
    d = _find_divisor(n)
    _split(d, factors)
    _split(n // d, factors)


def factor(n: int) -> dict[int, int]:
    """Prime factorisation of n as {prime: exponent}; {} for 1.

    Task: T064. Covers: FR-014.
    """
    factors: dict[int, int] = {}
    _split(_strip_small(n, factors), factors)
    return dict(sorted(factors.items()))


def modinv(a: int, m: int) -> int | None:
    """The inverse of a modulo m, or None when gcd(a, m) is not 1.

    Task: T080. Covers: FR-039.
    """
    try:
        return pow(a, -1, m)
    except ValueError:
        return None


def solve_linear(a: int, b: int, m: int) -> list[int]:
    """Every x in [0, m) with a*x = b (mod m): none, or gcd(a, m) of them.

    Task: T080. Covers: FR-039, FR-043.
    """
    g = gcd(a, m)
    if b % g != 0:
        return []
    step = m // g
    inverse = modinv(a // g, step)
    first = 0 if inverse is None else (b // g) * inverse % step
    return [first + k * step for k in range(g)]
