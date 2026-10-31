# References and decisions — lcgkit specification

Sources read for this specification. PDF page numbers refer to the PDF page index of NIST SP 800-22 Rev. 1a, not the printed page numbers.

## 1. Quality-verdict thresholds (FR-035 to FR-037)

| Decision | Value | Source | Status |
|---|---|---|---|
| Significance level | 0.01 | NIST SP 800-22 Rev. 1a, p.16: "Typically, α is chosen in the range [0.001, 0.01]." Decision rule at the 1% level: §2.2.5, p.27. | Cited (primary) |
| Pass rule | p ≥ α passes | Same, p.16: "If P-value ≥ α, then the null hypothesis is accepted" | Cited (primary) |
| Expected false-alarm rate | about 1% per check | Same, p.89: "if the significance level is chosen to be 0.01 (i.e., α = 0.01), then about 1 % of the sequences are expected to fail." | Cited (primary) |
| Chi-square p-value | upper-tail probability, `bins - 1` degrees of freedom | Same, §2.2.4, p.27: "P-value = igamc (N/2, χ2(obs)/2)". Verified against NIST/SEMATECH critical values at 1, 2, 3, 10 and 100 degrees of freedom (6.635, 9.210, 11.345, 23.209, 135.807) | Cited (primary) + verified |
| Serial-correlation limit | `2.576 / sqrt(N)` | NIST/SEMATECH e-Handbook, autocorrelation plot page: recommended band `± z(1-α/2) / sqrt(N)`; the page gives the same definition of `r_h` as FR-032. 2.576 is the 99.5th percentile of the standard normal distribution (computed: 2.5758) | Cited (primary) + computed |
| Minimum expected count per bin | 10 | The NIST e-Handbook chi-square page gives no minimum (it says only "sufficient sample size"; its example uses about 10 per bin). Wikipedia, "Pearson's chi-squared test": acceptable if no more than 20% of expected frequencies are below 5, and unreliable below 10 when there is 1 degree of freedom. 10 satisfies both. | Secondary only |
| Statement that passing proves nothing | stated in every report | NIST SP 800-22, p.11: "no set of statistical tests can absolutely certify a generator as appropriate for usage in a particular application, i.e., statistical testing cannot serve as a substitute for cryptanalysis." p.15: "no specific finite set of tests is deemed 'complete.'" | Cited (primary) |

URLs: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-22r1a.pdf ; https://www.itl.nist.gov/div898/handbook/eda/section3/eda3674.htm ; https://www.itl.nist.gov/div898/handbook/eda/section3/autocopl.htm ; https://www.itl.nist.gov/div898/handbook/eda/section3/eda35f.htm ; https://en.wikipedia.org/wiki/Pearson%27s_chi-squared_test

## 2. Decisions without an external source

1. **Minimum sample size of 100 for the independence check.** NIST gives no minimum for this check. The only precedent is NIST's recommendation of at least 100 bits for its frequency tests (§2.1.7, p.25), which is a different test.
2. **The period-covers-sample check.** A definition, not a statistical threshold: if the period is shorter than the sample, values repeat inside the sample.
3. **The three verdict levels** `no-defect-detected`, `caution`, `defect-detected` and the rule that a power-of-two modulus alone raises `caution`.
4. **Single-sample judgement.** NIST SP 800-22 tests many sequences and checks the proportion that pass and the uniformity of the p-values (its section 4.2); this specification judges one sample.

## 3. Facts about the generators

| Claim | Source | Status |
|---|---|---|
| Hull–Dobell conditions for a full period | Hull, T. E. and Dobell, A. R. (1962), "Random Number Generators", SIAM Review 4(3), 230–254; Knuth, TAOCP Vol. 2, 3rd ed., pp. 17–19 (both as cited by Wikipedia, "Linear congruential generator") | Secondary; independently verified by brute force on all 89,439 triples with 2 ≤ m ≤ 64 |
| Low `k` bits of a power-of-two LCG with `c ≠ 0` have period `2^k` | Wikipedia, "Linear congruential generator" | Secondary; verified for `glibc-type0` (periods 2, 4, 8) |
| RANDU is a poor generator | Press et al., Numerical Recipes in Fortran 77, 2nd ed., p.268 (as cited by Wikipedia) | Secondary |
| `glibc-type0` is the simple LCG used only when the state is 8 bytes | Wikipedia footnote citing glibc `stdlib/random_r.c` | Secondary |
| `minstd` / `minstd-new` parameters (16807 / 48271, m = 2^31 - 1, default seed 1) | cppreference, `std::linear_congruential_engine` | Secondary |
| 10,000th outputs 1043618065 / 399268537 from seed 1 | Not stated on cppreference; believed to be required by the C++ standard ([rand.predef]) but not confirmed against the standard's text | Unverified in a source; reproduced by an independent calculation |
| `numrec` parameters (1664525, 1013904223, m = 2^32) | Wikipedia, citing Numerical Recipes `ranqd1`, section 7.1, "from Knuth and H. W. Lewis" | Secondary |
| `mmix` multiplier 6364136223846793005 | MMIX Supplement `rsixfour.c`: "see TAOCP Vol 2, 3.3.4, page 108" | Primary pointer to Knuth; book not consulted |
| `mmix` increment 1442695040888963407 | PCG reference code (`PCG_DEFAULT_INCREMENT_64`, no credit to Knuth in the code); a secondary paper calls the pair "Knuth's MMIX LCG" | **Unverified against Knuth.** `rsixfour.c` uses 9754186451795953191, commented "some random start value" |

## 4. Not consulted

- Knuth, TAOCP Vol. 2 (3rd ed.): a lawful copy was not available; a copy from a piracy site was deliberately not used.
- NIST SP 800-22 printed page numbers (PDF page indices are used instead).
