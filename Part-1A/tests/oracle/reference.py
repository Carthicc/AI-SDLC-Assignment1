"""Reference calculations written without any code from src/. Slow and obvious on purpose."""

from __future__ import annotations

# NIST SP 800-22 / standard tables: upper 1% point of the chi-square distribution, by degrees
# of freedom.
NIST_CRITICAL_1_PERCENT = {1: 6.635, 2: 9.210, 10: 23.209, 100: 135.807}

# Published 10,000th outputs of the two Park-Miller generators started from seed 1.
MINSTD_10000TH = 1043618065
MINSTD_NEW_10000TH = 399268537


def step_sequence(a: int, c: int, m: int, x: int, n: int) -> list[int]:
    """Step x -> (a*x + c) mod m, n times, and return the n new values (the seed is not in it)."""
    values = []
    for _ in range(n):
        x = (a * x + c) % m
        values.append(x)
    return values


def brute_period(a: int, c: int, m: int, seed: int) -> int:
    """Length of the cycle the generator falls into from `seed`, found by remembering states."""
    seen: dict[int, int] = {}
    x, index = seed, 0
    while x not in seen:
        seen[x] = index
        x = (a * x + c) % m
        index += 1
    return index - seen[x]


def full_period_by_brute_force(a: int, c: int, m: int) -> bool:
    """True exactly when the cycle from seed 0 visits all m states."""
    return brute_period(a, c, m, 0) == m


def trial_factor(n: int) -> dict[int, int]:
    """Prime factorisation of n by trial division, as {prime: exponent}. For n up to 10**12."""
    factors: dict[int, int] = {}
    divisor = 2
    while divisor * divisor <= n:
        while n % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            n //= divisor
        divisor += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def chi_square(values: list[int], m: int, bins: int) -> float:
    """Chi-square statistic of `values` over `bins` equal-width bins of [0, m)."""
    counts = [0] * bins
    for value in values:
        counts[value * bins // m] += 1
    expected = len(values) / bins
    return sum((seen - expected) ** 2 / expected for seen in counts)


def lag1_autocorrelation(values: list[int], m: int) -> float | None:
    """Lag-1 serial correlation of u = value / m; None when the sequence is constant."""
    if len(set(values)) == 1:
        return None
    u = [value / m for value in values]
    mean = sum(u) / len(u)
    denominator = sum((x - mean) ** 2 for x in u)
    numerator = sum((u[t] - mean) * (u[t + 1] - mean) for t in range(len(u) - 1))
    return numerator / denominator


def low_bit_period(values: list[int], bits: int) -> int:
    """Smallest p so that the lowest `bits` bits of the sequence repeat every p steps.

    Needs at least 2p values to mean anything.
    """
    mask = (1 << bits) - 1
    low = [value & mask for value in values]
    for p in range(1, len(low)):
        if all(low[i] == low[i + p] for i in range(len(low) - p)):
            return p
    return len(low)


def closed_form_state(a: int, c: int, m: int, x: int, n: int) -> int:
    """State after n steps from x, by the closed form (no stepping and no doubling of the map).

    For a > 1, x_n = (a**n * (x*(a-1) + c) - c) / (a-1); the division is exact, so working modulo
    m*(a-1) and dividing afterwards gives the right value modulo m. For a = 1, x_n = x + n*c.
    """
    if a == 1:
        return (x + n * c) % m
    modulus = m * (a - 1)
    return ((pow(a, n, modulus) * (x * (a - 1) + c) - c) % modulus // (a - 1)) % m
