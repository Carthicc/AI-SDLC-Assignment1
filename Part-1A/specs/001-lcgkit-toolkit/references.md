# References and decisions — lcgkit specification

Sources read for this specification. NIST SP 800-22 page numbers are PDF page indices. Knuth page numbers are the printed page numbers of *The Art of Computer Programming*, Vol. 2, Seminumerical Algorithms, 3rd edition (Addison–Wesley), read from a copy I had.

## 1. Quality-verdict thresholds (FR-035 to FR-037)

| Decision | Value | Source | Status |
|---|---|---|---|
| Significance level | 0.01 | NIST SP 800-22 Rev. 1a, p.16: "Typically, α is chosen in the range [0.001, 0.01]." Decision rule at the 1% level: §2.2.5, p.27. | Cited (primary) |
| Pass rule | p ≥ α passes | Same, p.16: "If P-value ≥ α, then the null hypothesis is accepted" | Cited (primary) |
| Expected false-alarm rate | about 1% per check | Same, p.89: "if the significance level is chosen to be 0.01 (i.e., α = 0.01), then about 1 % of the sequences are expected to fail." | Cited (primary) |
| Chi-square p-value | upper-tail probability, `bins - 1` degrees of freedom | NIST SP 800-22 §2.2.4, p.27: "P-value = igamc (N/2, χ2(obs)/2)". Critical values at 1% agree in three independent places: NIST/SEMATECH e-Handbook table (1: 6.635, 2: 9.210, 3: 11.345, 10: 23.209, 100: 135.807), Knuth §3.3.1 Table 1, p.44 (1: 6.635, 2: 9.210, 3: 11.34), and our own computation. | Cited (primary) + verified |
| Serial-correlation definition and limit | lag-1 autocorrelation, limit `2.576 / sqrt(N)` | NIST/SEMATECH e-Handbook, autocorrelation page: `r_h = C_h / C_0` and the randomness band `± z(1-α/2) / sqrt(N)`; 2.576 is the 99.5th percentile of the normal distribution (computed: 2.5758). Knuth §3.3.2 test K, pp.72–73, defines a similar coefficient `C` with a cyclic sum and a good range of `μ_n ± 2σ_n` (about 95%); the two definitions are close for large `N` but not identical (see decision 5 in section 2). | Cited (primary), with a recorded difference |
| Minimum expected count per bin | 10 | Knuth §3.3.1, p.45: "A common rule of thumb is to take n large enough so that each of the expected values np_s is five or more; preferably, however, take n much larger than this." The NIST e-Handbook chi-square page gives no minimum. 10 is stricter than Knuth's 5 and also satisfies Wikipedia's note ("Pearson's chi-squared test") that with 1 degree of freedom counts below 10 are unreliable. | Cited (primary: 5); 10 is my choice |
| Statement that passing proves nothing | stated in every report | NIST SP 800-22, p.11: "no set of statistical tests can absolutely certify a generator as appropriate for usage in a particular application, i.e., statistical testing cannot serve as a substitute for cryptanalysis." p.15: "no specific finite set of tests is deemed 'complete.'" | Cited (primary) |

URLs: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-22r1a.pdf ; https://www.itl.nist.gov/div898/handbook/eda/section3/eda3674.htm ; https://www.itl.nist.gov/div898/handbook/eda/section3/autocopl.htm ; https://www.itl.nist.gov/div898/handbook/eda/section3/eda35f.htm

## 2. Decisions without an external source

1. **Minimum sample size of 100 for the independence check.** NIST gives no minimum for this check. The only precedent is NIST's recommendation of at least 100 bits for its frequency tests (§2.1.7, p.25), which is a different test.
2. **The period-covers-sample check.** A definition, not a statistical threshold: if the period is shorter than the sample, values repeat inside the sample.
3. **The three verdict levels** `no-defect-detected`, `caution`, `defect-detected`, and the rule that a power-of-two modulus alone raises `caution`.
4. **Single-sample judgement.** NIST SP 800-22 tests many sequences and checks the proportion that pass and the uniformity of the p-values (its section 4.2); this specification judges one sample.
5. **Serial-correlation definition.** The specification uses the non-cyclic definition from the NIST/SEMATECH e-Handbook with a 99% band, to stay consistent with the 0.01 significance level used for the chi-square check. Knuth's test K uses a cyclic sum and a 95% band.
6. **Minimum expected count of 10** (stricter than the 5 that Knuth gives as a rule of thumb).

## 3. Facts about the generators

| Claim | Source | Status |
|---|---|---|
| Full period if and only if `c` is coprime with `m`, `a - 1` is a multiple of every prime dividing `m`, and a multiple of 4 when `m` is | Knuth §3.2.1.2, **Theorem A**, p.17 (credits Greenberger 1961 for `m = 2^e` and Hull and Dobell, SIAM Review 4 (1962), 230–254, for the general case) | Cited (primary); also verified by brute force on all 89,439 triples with 2 ≤ m ≤ 64 |
| For `m = 2^e` the low-order bits are much less random; the lowest bit is constant or strictly alternating; the low `k` bits have period at most `2^k`; this does not happen when `m` is `w ± 1` | Knuth §3.2.1.1, p.13, equation (4) | Cited (primary); verified for `glibc-type0` (periods 2, 4, 8) |
| Use the high-order part of a word, and obtain an integer in `0..k-1` as `floor(k U)` | Knuth §3.4.1, p.119 | Cited (primary) |
| RANDU `X(n+1) = 65539 X(n) mod 2^31`, with `X0` odd, satisfies `9 X(n) - 6 X(n+1) + X(n+2) ≡ 0 (mod 2^31)` and "should never have been used" | Knuth §3.3.4, p.107, equation (37) | Cited (primary) |
| Multiplier `6364136223846793005` for modulus 2^64 | Knuth §3.3.4, Table 1 and its notes, p.108: "line 26 (whose excellent multiplier 6364136223846793005 …) is due to C. E. Haynes." Knuth lists multipliers only; **the book contains no increment and does not call this generator MMIX** (the book mentions MMIX only as a future computer, p.227) | Cited (primary) |
| `a = 6364136223846793005, c = 1, m = 2^64`, returning the top 31 bits (`state >> 33`) | musl C library, `src/prng/rand.c` (https://git.musl-libc.org/cgit/musl/plain/src/prng/rand.c) | Cited (primary source code) |
| `a = 6364136223846793005, c = 1442695040888963407, m = 2^64` | PCG reference code, `pcg_variants.h`: `PCG_DEFAULT_MULTIPLIER_64` and `PCG_DEFAULT_INCREMENT_64` (no credit to Knuth in that code) | Cited (primary source code); lineage to Knuth unverified |
| `minstd` / `minstd-new` parameters (16807 / 48271, m = 2^31 - 1, default seed 1); Park–Miller / Lewis–Goodman–Miller history | cppreference, `std::linear_congruential_engine`; Knuth p.108 notes on 16807 (Lewis, Goodman and Miller, IBM Systems J. 8 (1969)) | Cited (secondary / primary) |
| 10,000th outputs 1043618065 / 399268537 from seed 1 | Not stated on cppreference; believed to be required by the C++ standard ([rand.predef]) but not confirmed against the standard's text | Unverified in a source; reproduced by an independent calculation |
| `glibc-type0` is the simple LCG used only when the state is 8 bytes (a = 1103515245, c = 12345, m = 2^31) | Wikipedia footnote citing glibc `stdlib/random_r.c` | Secondary |
| `numrec` parameters (1664525, 1013904223, m = 2^32) | Wikipedia, citing Numerical Recipes `ranqd1`, section 7.1, "from Knuth and H. W. Lewis" | Secondary |

## 4. Not consulted

- The C++ standard text ([rand.predef]) and the glibc source (`random_r.c`).
- Numerical Recipes (`ranqd1`).
- NIST SP 800-22 printed page numbers (PDF page indices are used instead).
- The copy of Knuth's book used here is not part of this repository and must not be committed to it; cite the book, not the file.
