"""Tests of the reference calculations themselves. No markers, nothing imported from src/."""

from math import prod

from tests.oracle import reference as ref


def test_small_example_matches_hand_calculation() -> None:
    assert ref.step_sequence(5, 3, 16, 7, 5) == [6, 1, 8, 11, 10]


def test_published_minstd_values() -> None:
    assert ref.step_sequence(16807, 0, 2**31 - 1, 1, 5) == [
        16807, 282475249, 1622650073, 984943658, 1144108930,
    ]
    assert ref.step_sequence(16807, 0, 2**31 - 1, 1, 10_000)[-1] == ref.MINSTD_10000TH
    assert ref.step_sequence(48271, 0, 2**31 - 1, 1, 10_000)[-1] == ref.MINSTD_NEW_10000TH


def test_trial_factor_known_factorisations() -> None:
    assert ref.trial_factor(1) == {}
    assert ref.trial_factor(360) == {2: 3, 3: 2, 5: 1}
    assert ref.trial_factor(2**31 - 1) == {2**31 - 1: 1}
    assert ref.trial_factor(2**31 - 2) == {2: 1, 3: 2, 7: 1, 11: 1, 31: 1, 151: 1, 331: 1}
    assert ref.trial_factor(10**12) == {2: 12, 5: 12}


def test_trial_factor_multiplies_back() -> None:
    for n in range(2, 2000):
        assert prod(p**e for p, e in ref.trial_factor(n).items()) == n


def test_brute_period() -> None:
    assert ref.brute_period(5, 3, 16, 0) == 16
    assert ref.brute_period(1, 0, 16, 3) == 1


def test_brute_period_counts_only_the_cycle() -> None:
    # 1 -> 2 -> 4 -> 8 -> 0 -> 0: the cycle is the single state 0
    assert ref.brute_period(2, 0, 16, 1) == 1


def test_full_period_by_brute_force() -> None:
    assert ref.full_period_by_brute_force(5, 3, 16)
    assert not ref.full_period_by_brute_force(1, 0, 16)


def test_brute_force_agrees_with_the_three_conditions() -> None:
    # The Hull-Dobell conditions, applied with the oracle's own factoring.
    for m in range(2, 33):
        primes = ref.trial_factor(m)
        for a in range(m):
            for c in range(m):
                coprime = all(c % p for p in primes)
                prime_ok = all((a - 1) % p == 0 for p in primes)
                four_ok = m % 4 != 0 or (a - 1) % 4 == 0
                assert ref.full_period_by_brute_force(a, c, m) == (coprime and prime_ok and four_ok)


def test_chi_square() -> None:
    assert ref.chi_square(list(range(16)), 16, 16) == 0
    assert ref.chi_square([3] * 16, 16, 16) == 240


def test_lag1_autocorrelation() -> None:
    assert ref.lag1_autocorrelation([5] * 10, 16) is None
    assert ref.lag1_autocorrelation([0, 8, 0, 8], 16) == -0.75


def test_low_bit_period_of_a_power_of_two_generator() -> None:
    values = ref.step_sequence(1103515245, 12345, 2**31, 1, 64)
    assert [ref.low_bit_period(values, bits) for bits in (1, 2, 3)] == [2, 4, 8]
