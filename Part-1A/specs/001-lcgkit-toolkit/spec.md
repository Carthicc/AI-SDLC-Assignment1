# Feature Specification: lcgkit — Linear Congruential Generator Toolkit

**Input**: User description: "A deterministic Linear Congruential Generator (LCG) toolkit. It generates reproducible sequences from custom or well-known parameters, validates parameter quality, jumps ahead in a sequence, draws unbiased bounded integers and unit floats, refuses security-sensitive uses, reports sequence quality, and is available as a library, a command line tool and a stateless HTTP service. Stretch capabilities: predict a sequence from observed outputs (to show why an LCG is insecure) and split a sequence into independent substreams."

## Terminology

- **Parameter set**: a multiplier `a`, an increment `c` and a modulus `m`.
- **Seed**: the starting state `x0`. It is **not** emitted as an output.
- **Step**: `x(n+1) = (a * x(n) + c) mod m`. Output number `k` is `x(k)`; the first output is `x(1)`.
- **Next state**: the state after the last emitted output (the seed if nothing was emitted). Passing it back as a seed continues the same sequence.
- **Full period**: the sequence visits all `m` values before repeating.
- **Interface**: one of the three ways of using the toolkit: *library*, *command line*, *HTTP service*.

## User Scenarios & Testing

Priorities: **P1** = core, **P2** = important extensions, **P3** = stretch. Each story is independently testable. Every scenario carries an acceptance-criterion ID (`AC-nnn`) that tests and tasks must cite, and names the requirements it covers.

### User Story 1 - Generate a reproducible sequence (Priority: P1)

A developer supplies a parameter set, a seed and a count, and receives that many generator outputs plus the next state, so the same request always gives the same numbers and a later request can continue where this one stopped.

**Why this priority**: Everything else builds on correct, reproducible generation.

**Independent Test**: Run the worked example `a=5, c=3, m=16, seed=7` and compare with the listed values; run the invalid-input table and compare error codes.

**Acceptance Scenarios**:

1. **AC-001** (FR-002, FR-003) **Given** `a=5, c=3, m=16, seed=7`, **When** 5 values are requested, **Then** the outputs are `[6, 1, 8, 11, 10]` and the next state is `10`.
2. **AC-002** (FR-003) **Given** the result of AC-001, **When** 3 more values are requested using its next state as the seed, **Then** the outputs are `[5, 12, 15]`, and asking for 8 values in one request returns `[6, 1, 8, 11, 10, 5, 12, 15]`.
3. **AC-003** (FR-004) **Given** any valid parameter set and seed, **When** 0 values are requested, **Then** the output list is empty and the next state equals the seed.
4. **AC-004** (FR-005) **Given** any valid request, **When** it is sent 100 times, **Then** all 100 results are byte-for-byte identical.
5. **AC-005** (FR-001, FR-007) **Given** `m=1`, **When** a sequence is requested, **Then** the error code is `invalid-modulus` and no values are returned. The same holds for `m=2^64+1`.
6. **AC-006** (FR-001, FR-007) **Given** `m=16` and `a=16`, **Then** the error code is `invalid-multiplier`; given `c=-1`, **Then** `invalid-increment`; given `seed=16`, **Then** `invalid-seed`.
7. **AC-007** (FR-007) **Given** any numeric field supplied as `3.5`, `"abc"`, `true` or `null`, **Then** the error code is `invalid-type` and the error names the offending field.
8. **AC-008** (FR-002) **Given** `m=2^64` with the MMIX parameters and seed 0, **When** 2 values are requested, **Then** the outputs are `[1442695040888963407, 1876011003808476466]` (no wrap-around error at the 64-bit boundary).
9. **AC-009** (FR-006) **Given** any successful request, **Then** the result contains the marker `cryptographically_secure: false`.
10. **AC-010** (FR-008) **Given** `c=0` and `seed=0`, **When** a sequence is requested, **Then** the outputs are all zero and the result carries the warning code `zero-fixed-point`; **given** `a` equal to 0 or 1, **Then** the result carries `degenerate-multiplier`.
11. **AC-011** (FR-004) **Given** a count of exactly 1,000,000, **Then** the request succeeds; **given** 1,000,001, **Then** the error code is `count-exceeds-limit`; a negative count gives `invalid-count`.

---

### User Story 2 - Use well-known presets (Priority: P1)

A developer picks a named, published generator instead of typing parameters, and can list what is available.

**Why this priority**: Presets give independently published reference values and make the toolkit useful on day one.

**Independent Test**: Request each preset with the listed seed and compare to the published or reference values below.

**Acceptance Scenarios**:

1. **AC-012** (FR-009) **Given** preset `minstd` (a=16807, c=0, m=2^31-1) and seed 1, **When** 5 values are requested, **Then** the outputs are `[16807, 282475249, 1622650073, 984943658, 1144108930]`, and the 10,000th output is `1043618065` (the published Park–Miller check value).
2. **AC-013** (FR-009) **Given** preset `minstd-new` (a=48271, c=0, m=2^31-1) and seed 1, **Then** the first 3 outputs are `[48271, 182605794, 1291394886]` and the 10,000th output is `399268537` (the published check value).
3. **AC-014** (FR-009) **Given** preset `glibc-type0` (a=1103515245, c=12345, m=2^31) and seed 1, **Then** the first 3 outputs are `[1103527590, 377401575, 662824084]`.
4. **AC-015** (FR-009) **Given** preset `numrec` (a=1664525, c=1013904223, m=2^32) and seed 0, **Then** the first 3 outputs are `[1013904223, 1196435762, 3519870697]`.
5. **AC-016** (FR-009) **Given** preset `mmix` (a=6364136223846793005, c=1442695040888963407, m=2^64) and seed 0, **Then** the first 2 outputs are `[1442695040888963407, 1876011003808476466]`.
6. **AC-017** (FR-009) **Given** preset `randu` (a=65539, c=0, m=2^31) and seed 1, **Then** the first 4 outputs are `[65539, 393225, 1769499, 7077969]`.
7. **AC-018** (FR-010) **When** the preset list is requested, **Then** exactly the six presets above are returned, each with its `a`, `c`, `m` and a one-line description, in the order listed here.
8. **AC-019** (FR-011) **Given** any preset, **Then** a request by preset name returns exactly the same result as a request with that preset's parameters written out.
9. **AC-020** (FR-012) **Given** a preset name that does not exist, **Then** the error code is `unknown-preset`.

---

### User Story 3 - Check whether parameters are any good (Priority: P1)

A developer submits a parameter set and learns whether it reaches a full period, and if not, exactly which rule it breaks.

**Why this priority**: It is the toolkit's core educational and diagnostic value and the most testable piece, because a brute-force walk of the whole cycle gives an independent answer for small moduli.

**Independent Test**: Compare verdicts with a brute-force period measurement for every small parameter triple.

**Acceptance Scenarios**:

1. **AC-021** (FR-013, FR-014) **Given** `a=1103515245, c=24680, m=2^31` (the glibc multiplier with an even increment), **When** validated, **Then** the verdict is `not-full-period` with exactly one reason: `increment-not-coprime`.
2. **AC-022** (FR-013, FR-016) **Given** the presets `glibc-type0`, `numrec` and `mmix`, **Then** each verdict is `full-period` with expected period equal to its `m`, and no reasons.
3. **AC-023** (FR-014) **Given** the preset `minstd` (c=0), **Then** the verdict is `not-full-period` with the reasons `increment-not-coprime` and `multiplier-minus-one-not-divisible-by-prime-factor`, in that order.
4. **AC-024** (FR-015) **Given** every parameter triple with `2 <= m <= 64` and `0 <= a, c < m` (89,439 triples), **Then** the verdict equals the brute-force result (full period exactly when the measured period from seed 0 is `m`) with zero disagreements.
5. **AC-025** (FR-014) **Given** `m=16, a=3, c=1`, **Then** the verdict is `not-full-period` with the reason `multiplier-minus-one-not-divisible-by-four` only.
6. **AC-026** (FR-017) **Given** any valid parameter set, **Then** the result lists the outcome (pass or fail) of each of the three conditions separately.
7. **AC-027** (FR-013) **Given** `m=2, a=1, c=1`, **Then** the verdict is `full-period` (smallest valid modulus).
8. **AC-028** (FR-001, FR-007) **Given** invalid parameters, **Then** the same error codes as in AC-005 to AC-007 are returned.

---

### User Story 4 - Jump ahead in a sequence (Priority: P1)

A developer asks for the state after `n` steps without generating the `n-1` values in between, even when `n` is astronomically large.

**Why this priority**: It is a classic LCG capability, easy to get subtly wrong, and it underpins independent substreams.

**Independent Test**: For small `n`, compare jump-ahead with stepping `n` times; for large `n`, use known identities.

**Acceptance Scenarios**:

1. **AC-029** (FR-018, FR-019) **Given** each preset and the seed 1, **When** jumping `n` steps for every `n` from 0 to 1000, **Then** the state equals the state reached by stepping `n` times, for every preset and every `n`.
2. **AC-030** (FR-018) **Given** `minstd` and seed 1, **When** jumping 10000 steps, **Then** the state is `1043618065`.
3. **AC-031** (FR-018) **Given** `n=0`, **Then** the result equals the seed.
4. **AC-032** (FR-019) **Given** `glibc-type0` and any seed, **When** jumping `2^31` steps (its full period), **Then** the state equals the seed; jumping `2^31 + 5` steps equals jumping 5 steps.
5. **AC-033** (FR-018) **Given** any `n1`, `n2` in range, **Then** jumping `n1` and then `n2` from the resulting state equals jumping `n1 + n2` in one go.
6. **AC-034** (FR-018, FR-021) **Given** `n = 2^64 - 1`, **Then** the jump succeeds; **given** `n = 2^64` or a negative `n`, **Then** the error code is `invalid-jump`.
7. **AC-035** (FR-020) **Given** any `n < 2^64`, **Then** the jump uses at most 64 modular multiplications.

---

### User Story 5 - Draw unbiased bounded integers and unit floats (Priority: P1)

A developer asks for whole numbers inside an inclusive range (for example a die roll) or for fractions in `[0, 1)`, without favouring any value.

**Why this priority**: Rounding a scaled value makes the two end values half as likely as the others, and taking a remainder leans on the weak low bits of power-of-two moduli.

**Independent Test**: Use the small full-period example and count how often each value appears over exactly one period.

**Acceptance Scenarios**:

1. **AC-036** (FR-022, FR-023) **Given** `a=5, c=3, m=16, seed=7` and the range 1 to 3, **When** exactly one full period (16 outputs) is consumed, **Then** the values 1, 2 and 3 each appear exactly 5 times, 1 output was discarded, and the result reports 16 outputs consumed.
2. **AC-037** (FR-023) **Given** the same generator and every range size from 1 to 16, **Then** over one full period every value in the range appears exactly the same number of times.
3. **AC-038** (FR-022) **Given** the range -3 to 3, **Then** every value is within the range and negative bounds are accepted.
4. **AC-039** (FR-025) **Given** a range with a single value (`lo = hi`), **Then** that value is returned for every draw, no output is consumed and the state is unchanged.
5. **AC-040** (FR-024) **Given** `lo > hi`, **Then** the error code is `invalid-range`; **given** a range with more values than `m`, **Then** `range-exceeds-modulus`.
6. **AC-041** (FR-023) **Given** `glibc-type0`, seed 1 and the range 0 to 1, **When** 64 values are drawn, **Then** the values do not strictly alternate (the weak low bit must not dominate the result).
7. **AC-042** (FR-027) **Given** any generator and range, **Then** drawing 10 values in one request equals drawing 4 and then 6 using the reported next state.
8. **AC-043** (FR-026) **Given** `a=5, c=3, m=16, seed=7`, **When** 5 unit floats are requested, **Then** they are `[0.375, 0.0625, 0.5, 0.6875, 0.625]`.
9. **AC-044** (FR-026) **Given** the MMIX parameters and a seed whose next output is `m-1` (seed `15635871386175874928`), **Then** the unit float is strictly less than 1.0.
10. **AC-045** (FR-007) **Given** non-integer bounds, **Then** the error code is `invalid-type`.

---

### User Story 6 - Refuse security-sensitive uses (Priority: P2)

A developer who declares that the numbers are for a token, key, password or similar is refused and pointed to a cryptographically secure source.

**Why this priority**: An LCG is predictable. The toolkit must never help someone build a weak secret, and the constitution (Principle V) requires this refusal.

**Independent Test**: Send requests with a range of purpose labels and check which are refused.

**Acceptance Scenarios**:

1. **AC-046** (FR-028, FR-029) **Given** a purpose label of `token`, `Session Token`, `KEYS` or `api-key`, **When** any generation is requested, **Then** the request is refused with the error code `insecure-purpose`, no values are returned, and the message recommends a cryptographically secure source.
2. **AC-047** (FR-030) **Given** the labels `dice`, `monkey business`, `simulation`, or no label at all, **Then** the request is accepted (matching is by whole word, so `monkey` does not match `key`).
3. **AC-048** (FR-029) **Given** each refused word in singular and plural form (`token`, `key`, `password`, `secret`, `session`, `nonce`, `salt`, `credential`, `otp`), **Then** all are refused.
4. **AC-049** (FR-031) **Then** the documentation states that the guard depends on the declared purpose and cannot detect undeclared misuse.

---

### User Story 7 - Report sequence quality (Priority: P2)

A developer asks for a small, fixed set of measurements on a generator's output to see why one parameter set is better than another.

**Why this priority**: It turns the validator's theory into numbers, and shows weaknesses such as the short cycle of low bits.

**Independent Test**: Use tiny generators where every number can be computed by hand.

**Acceptance Scenarios**:

1. **AC-050** (FR-032) **Given** `a=5, c=3, m=16, seed=7`, sample size 16 and 16 bins, **Then** the measured period is 16 and the chi-square statistic is exactly 0.
2. **AC-051** (FR-032) **Given** `a=1, c=0, m=16, seed=3`, sample size 16 and 16 bins, **Then** the measured period is 1 and the chi-square statistic is exactly 240.
3. **AC-052** (FR-032) **Given** a constant sequence, **Then** the serial correlation is reported as `undefined` (never a not-a-number value or a crash).
4. **AC-053** (FR-032) **Given** `glibc-type0` and seed 1, **Then** the period of the lowest bit is 2, of the lowest 2 bits is 4 and of the lowest 3 bits is 8.
5. **AC-054** (FR-032) **Given** a modulus that is not a power of two (for example `minstd`), **Then** the low-bit periods are reported as `not-applicable`.
6. **AC-055** (FR-032) **Given** `m` above 2^24, **Then** the measured period is reported as `not-computed` and the remaining metrics are still returned.
7. **AC-056** (FR-034) **Given** a sample size below 2 or a bin count below 1 or above the sample size, **Then** the error codes are `invalid-count` and `invalid-bins`.
8. **AC-057** (FR-033) **Given** any quality request repeated, **Then** every reported number is identical across repeats and matches an independent reference calculation to a relative tolerance of 1e-9.
9. **AC-058** (FR-035) **Given** `minstd`, seed 1, sample size 10,000 and 10 bins, **Then** the chi-square statistic is 6.69, the p-value is 0.6694 (to the digits shown), the serial correlation is -0.0005 (to the digits shown), every check passes and the verdict is `no-defect-detected`.
10. **AC-059** (FR-035) **Given** `glibc-type0`, seed 1, sample size 10,000 and 10 bins, **Then** the chi-square statistic is 8.882, the p-value is 0.4482, the serial correlation is -0.00111, no check fails, the low-bits flag `low-bits-short-period` is raised and the verdict is `caution`.
11. **AC-060** (FR-035) **Given** `a=1, c=0, m=16, seed=3` and sample size 16, **Then** the check period-covers-sample fails (period 1 is below 16) and the verdict is `defect-detected`.
12. **AC-061** (FR-035) **Given** `a=5, c=3, m=16, seed=7`, sample size 16 and 16 bins, **Then** uniformity and independence are `not-applicable`, period-covers-sample passes and the verdict is `caution`.
13. **AC-062** (FR-036) **Given** the published 1% critical values 6.635 (1 degree of freedom), 9.210 (2), 23.209 (10) and 135.807 (100), **Then** the p-value computed for each is 0.01 within 0.0005.
14. **AC-063** (FR-037) **Given** any quality report, **Then** it contains the statement that passing the checks does not establish randomness or security.
15. **AC-064** (FR-034) **Given** a sample size of exactly 1,000,000, **Then** the report succeeds; **given** 1,000,001, **Then** the error code is `count-exceeds-limit`.

---

### User Story 8 - Use it from the command line (Priority: P2)

A user runs the toolkit from a terminal, gets readable output by default and structured output on request, and can rely on exit statuses in scripts.

**Why this priority**: It makes the toolkit usable without writing code and is the easiest way to demonstrate it.

**Independent Test**: Run the command line with the worked examples and check output, exit status and stream.

**Acceptance Scenarios**:

1. **AC-065** (FR-038) **Given** each capability above, **Then** it can be invoked from the command line.
2. **AC-066** (FR-039, FR-042) **Given** the structured-output option, **Then** the output parses as JSON and equals the library result for the same input.
3. **AC-067** (FR-039) **Given** no option, **Then** the output is human-readable text containing the same values.
4. **AC-068** (FR-040) **Given** success, **Then** the exit status is 0; **given** invalid input, **Then** it is non-zero; **given** a refused purpose, **Then** it is non-zero and different from the invalid-input status.
5. **AC-069** (FR-041) **Given** an error, **Then** the message is written to the error stream and nothing is written to the result stream.

---

### User Story 9 - Use it as an HTTP service (Priority: P2)

A client calls the toolkit over HTTP. Every request carries all its input, nothing is stored between requests, and a published interface description matches the real behaviour.

**Why this priority**: It is the service form of the toolkit and the basis of the constitution's contract-test gate.

**Independent Test**: Send the shared example set to the service and run contract checks derived from the interface description.

**Acceptance Scenarios**:

1. **AC-070** (FR-043) **Given** each capability above, **Then** it is available as a request/response operation.
2. **AC-071** (FR-044) **Given** two identical requests, **Then** the response bodies are byte-for-byte identical, and a continuation request using a returned next state matches a single longer request.
3. **AC-072** (FR-045) **Given** invalid input, **Then** the response is a client-error status with the structured error body; **given** a refused purpose, **Then** the client-error status differs from the invalid-input status.
4. **AC-073** (FR-047) **Given** malformed JSON, missing fields, unknown fields, wrong types, oversized numbers or empty bodies, **Then** the response is a structured client error with code `malformed-request` or the specific code, and **never** a server error.
5. **AC-074** (FR-046) **Given** the published interface description, **Then** automatically generated contract tests find no mismatch between it and the behaviour.
6. **AC-075** (FR-042) **Given** the shared example set, **Then** the service results equal the library results.

---

### User Story 10 - Predict a sequence from its outputs (Priority: P3, stretch)

A learner supplies observed outputs of an LCG and the toolkit recovers what is hidden and predicts what comes next, demonstrating why an LCG must never protect a secret. Three situations are supported: (A) the modulus is known and the outputs are complete; (B) the modulus is unknown and the outputs are complete; (C) the parameters are known but the outputs are truncated to their high-order bits (as in some C library `rand()` implementations).

**Why this priority**: It makes the security message concrete, but the toolkit is complete without it. It is the riskiest story and may be reduced or dropped without affecting the rest.

**Independent Test**: Generate outputs from a known preset, hide what the predictor is not told, and check that it reproduces the future outputs.

**Acceptance Scenarios**:

1. **AC-076** (FR-048, FR-051) **Given** `m=2^31` and the first 5 outputs of `glibc-type0` from seed 1, **Then** the recovered parameters are `a=1103515245, c=12345` and the next 10 predicted values equal the generator's next 10 outputs.
2. **AC-077** (FR-052) **Given** only 2 outputs and a known modulus, **Then** the error code is `insufficient-data`.
3. **AC-078** (FR-052) **Given** `m=16` and the outputs `[0, 0, 0]`, where several multipliers fit, **Then** the error code is `ambiguous-parameters` and no guess is returned.
4. **AC-079** (FR-049, FR-051) **Given** no modulus and the first 12 outputs of `glibc-type0` from seed 1, **Then** the recovered modulus is `2^31`, the recovered parameters are `a=1103515245, c=12345` and the next 10 predicted values equal the generator's next 10 outputs.
5. **AC-080** (FR-049, FR-051) **Given** no modulus and the first 12 outputs of `mmix` from seed 0, **Then** the recovered modulus is `2^64` and the next 10 predicted values equal the generator's next 10 outputs.
6. **AC-081** (FR-049, FR-052) **Given** no modulus and fewer than 12 outputs, **Then** the error code is `insufficient-data`.
7. **AC-082** (FR-050, FR-051) **Given** `glibc-type0` (parameters known), 16 hidden low-order bits and the first 4 outputs of seed 1 shifted right by 16 (15 visible bits each), **Then** the full internal state is recovered and the next 10 full-width outputs are predicted correctly.
8. **AC-083** (FR-050, FR-052) **Given** the same setting but only the first 2 truncated outputs, **Then** two states fit, the error code is `ambiguous-parameters` and no guess is returned.
9. **AC-084** (FR-050) **Given** truncated outputs together with unknown parameters, or more than 20 hidden bits, or a modulus that is not a power of two, **Then** the error code is `unsupported-combination`.
10. **AC-085** (FR-053) **Given** any successful prediction, **Then** the result states that it demonstrates the generator is insecure and that recovery of an unknown modulus is probable but not certain.

---

### User Story 11 - Split a sequence into independent substreams (Priority: P3, stretch)

A developer divides one sequence into several non-overlapping blocks (for example, one per worker) so parallel workers never reuse the same numbers.

**Why this priority**: It showcases jump-ahead, but nothing else depends on it.

**Independent Test**: Concatenate the substreams and compare with the plain sequence.

**Acceptance Scenarios**:

1. **AC-086** (FR-054, FR-055) **Given** `glibc-type0`, seed 1, 4 substreams of length 5, **Then** concatenating the substreams in order equals the first 20 outputs of the plain sequence.
2. **AC-087** (FR-054) **Given** the same request, **Then** each substream's starting state equals the jump-ahead state at `i * 5` for substream `i` (counting from 0).
3. **AC-088** (FR-056) **Given** a request where substreams times length exceeds `m`, **Then** the error code is `stream-exceeds-modulus`.
4. **AC-089** (FR-056) **Given** zero or negative substream counts or lengths, **Then** the error code is `invalid-count`.

---

### Edge Cases

- `m = 2` (smallest) and `m = 2^64` (largest) are accepted; `m = 1`, `m = 2^64 + 1` and negatives are not.
- `c = 0` with `seed = 0` is stuck at zero: accepted with a warning, never an error.
- `a = 0` or `a = 1` are accepted with a warning.
- A count of 0 returns an empty list and leaves the state unchanged.
- Very large integers, decimals, strings, booleans and `null` in any numeric field give a structured error, not a crash.
- A 64-bit modulus must not let a unit float round up to exactly 1.0 (AC-044).
- Power-of-two moduli have weak low bits; ranges must not simply take the remainder (AC-041).
- A range with one value consumes nothing (AC-039).
- Two requests with identical input must give identical output, regardless of order, timing or concurrency.
- A purpose label with extra spaces, mixed case or punctuation is normalised before matching.
- Quality reports on constant sequences must not divide by zero (AC-052).
- A legitimate result can be large: up to 1,000,000 values, roughly 20 MB of text for 64-bit values.

## Requirements

### Functional Requirements

**Generation (User Story 1)**

- **FR-001**: The system MUST accept a parameter set and seed only when `2 <= m <= 2^64`, `0 <= a < m`, `0 <= c < m` and `0 <= seed < m`, all integers.
- **FR-002**: The system MUST generate outputs by `x(n+1) = (a * x(n) + c) mod m`, exactly and without overflow for any accepted `m`, and MUST NOT emit the seed as an output.
- **FR-003**: Every generation result MUST include the next state so that a later request can continue the same sequence.
- **FR-004**: The system MUST accept a count `n` with `0 <= n <= 1,000,000`. A count of 0 MUST return an empty list and an unchanged state. The same limit of 1,000,000 applies to every operation that produces or consumes a list of values: sample size, substreams times length, outputs supplied to the predictor, and predicted values.
- **FR-005**: Identical input MUST produce byte-identical output on every run and every interface.
- **FR-006**: Every successful result MUST carry the marker `cryptographically_secure: false`.
- **FR-007**: Invalid input MUST produce a structured error with a stable `code`, a human-readable `message` and the offending `field`, and MUST NOT return partial results.
- **FR-008**: Degenerate configurations MUST be accepted and flagged with warning codes: `zero-fixed-point` (c = 0 and seed = 0) and `degenerate-multiplier` (a is 0 or 1).

**Presets (User Story 2)**

- **FR-009**: The system MUST provide the presets `minstd`, `minstd-new`, `glibc-type0`, `numrec`, `mmix` and `randu` with the parameters listed in AC-012 to AC-017.
- **FR-010**: The system MUST list all presets with their parameters and a one-line description.
- **FR-011**: A request using a preset name MUST be equivalent to one using that preset's written-out parameters.
- **FR-012**: An unknown preset name MUST be rejected with `unknown-preset`.

**Parameter validation (User Story 3)**

- **FR-013**: For any valid parameter set the system MUST return a verdict of `full-period` or `not-full-period`.
- **FR-014**: A `not-full-period` verdict MUST list every violated condition from `increment-not-coprime`, `multiplier-minus-one-not-divisible-by-prime-factor` and `multiplier-minus-one-not-divisible-by-four`, in that fixed order. These are the Hull–Dobell conditions: the increment is coprime with `m`; `a - 1` is divisible by every prime factor of `m`; `a - 1` is divisible by 4 when `m` is.
- **FR-015**: The verdict MUST agree with the true period for every parameter set (SC-002).
- **FR-016**: A `full-period` verdict MUST report the expected period (equal to `m`).
- **FR-017**: The result MUST report the pass or fail outcome of each condition separately.

**Jump-ahead (User Story 4)**

- **FR-018**: The system MUST return the state after `n` steps from a given state for `0 <= n < 2^64`.
- **FR-019**: The result MUST equal the state reached by stepping `n` times.
- **FR-020**: Per constitution Principle IV, jump-ahead MUST use at most 64 modular multiplications for any `n < 2^64`.
- **FR-021**: A jump distance outside the allowed range MUST be rejected with `invalid-jump`.

**Bounded integers and floats (User Story 5)**

- **FR-022**: The system MUST draw integers from an inclusive range `[lo, hi]`; negative bounds are allowed.
- **FR-023**: Drawing MUST be unbiased: over one full period of a full-period generator every value in the range occurs equally often. Rounding and plain remainder (which favour some values or the weak low bits) MUST NOT be used. Outputs that would cause bias MUST be discarded.
- **FR-024**: A range with `lo > hi` MUST be rejected with `invalid-range`; a range larger than `m` with `range-exceeds-modulus`.
- **FR-025**: A single-value range MUST return that value, consume no output and leave the state unchanged.
- **FR-026**: The system MUST produce unit floats in `[0, 1)` by dividing the output by `m`, and the result MUST never equal 1.0, even for a 64-bit modulus.
- **FR-027**: Results MUST report the number of outputs consumed and the next state, so splitting a request into parts gives the same values as one request.

**Misuse guard (User Story 6)**

- **FR-028**: Every generation operation MUST accept an optional `purpose` label.
- **FR-029**: A label MUST be normalised (trimmed, lower-cased, split on non-alphanumeric characters) and refused with `insecure-purpose` if any word is one of `token`, `key`, `password`, `secret`, `session`, `nonce`, `salt`, `credential`, `otp` or its plural. A refusal MUST return no values and MUST recommend a cryptographically secure source.
- **FR-030**: A missing label or one without such a word MUST be accepted.
- **FR-031**: The documentation MUST state that the guard relies on the declared purpose and cannot detect undeclared misuse.

**Quality report (User Story 7)**

- **FR-032**: Given a parameter set, seed, sample size `N` and bin count, the system MUST report: the measured period (when `m <= 2^24`, otherwise `not-computed`); the chi-square statistic over equal-width bins; the lag-1 serial correlation (`undefined` for a constant sequence); the periods of the lowest 1, 2 and 3 bits (when `m` is a power of two, otherwise `not-applicable`); the chi-square p-value; and the overall verdict defined in FR-035.
- **FR-033**: Quality results MUST be deterministic and match an independent reference calculation to a relative tolerance of 1e-9.
- **FR-034**: Sample size MUST be between 2 and 1,000,000 and bins between 1 and the sample size; otherwise `invalid-count`, `count-exceeds-limit` or `invalid-bins`.
- **FR-035**: The quality report MUST report each of the following checks with its measured value and an outcome of `pass`, `fail` or `not-applicable`, using fixed thresholds:
  - **period-covers-sample**: the measured period is at least the sample size (not-applicable when the period is `not-computed`);
  - **uniformity**: the chi-square p-value is at least 0.01 (not-applicable when the sample size divided by the bin count is below 5);
  - **independence**: the absolute lag-1 serial correlation is at most `2.576 / sqrt(N)` (not-applicable when `N` is below 100);
  - **low-bits**: flagged `low-bits-short-period` when `m` is a power of two (informational, never a failure).

  The overall verdict MUST be `defect-detected` if any applicable check fails; otherwise `caution` if the low-bits flag is raised; otherwise `no-defect-detected`. Thresholds are constants of this specification and MUST NOT be changed except by a documented amendment of this specification.
- **FR-036**: The chi-square p-value MUST be the upper-tail probability of the chi-square distribution with `bins - 1` degrees of freedom and MUST match the published 1% critical values (AC-062).
- **FR-037**: Every quality report MUST state that passing the checks does not establish randomness or security. The documentation MUST record the justification of the thresholds: significance level 0.01 (within the 0.001 to 0.01 range suggested by NIST SP 800-22); normal approximation for the serial correlation (99% two-sided, 2.576); a minimum expected count of 5 per bin; and the expected false-alarm rate of about 1% per statistical check on a sound generator.

**Command line (User Story 8)**

- **FR-038**: Every capability MUST be usable from the command line.
- **FR-039**: Output MUST be human-readable by default and JSON on request.
- **FR-040**: Exit status MUST be 0 on success and non-zero on failure, with different statuses for invalid input and for a refused purpose.
- **FR-041**: Results MUST go to the standard output and error messages to the standard error.
- **FR-042**: Results MUST be semantically identical across the library, the command line (JSON) and the HTTP service.

**HTTP service (User Story 9)**

- **FR-043**: Every capability MUST be available as a stateless request/response operation.
- **FR-044**: The service MUST NOT persist anything or depend on earlier requests; continuation uses the returned next state.
- **FR-045**: Invalid input MUST give a client-error status with the structured error body; a refused purpose MUST give a different client-error status.
- **FR-046**: A machine-readable interface description MUST be published and MUST match the behaviour (contract-tested).
- **FR-047**: No input, however malformed, may cause a server error; unparseable requests MUST return `malformed-request`.

**Predictor (User Story 10)**

- **FR-048** (mode A): Given a known modulus and at least 3 consecutive complete outputs, the system MUST recover the multiplier and increment when uniquely determined and predict the next `k` values.
- **FR-049** (mode B): Given no modulus and at least 12 consecutive complete outputs, the system MUST recover the modulus (a value larger than every supplied output), then the multiplier and increment, and predict the next `k` values.
- **FR-050** (mode C): Given known parameters whose modulus is a power of two, no more than 20 hidden low-order bits and truncated outputs, the system MUST recover the full internal state and predict the next `k` full-width values. Truncated outputs with unknown parameters are out of scope and MUST be rejected with `unsupported-combination`.
- **FR-051**: Recovered parameters or state MUST reproduce every supplied output.
- **FR-052**: Too few outputs MUST give `insufficient-data`; several equally valid solutions MUST give `ambiguous-parameters`, and no guess may be returned.
- **FR-053**: Every prediction MUST state that it demonstrates the generator is not secure, and mode B results MUST state that recovery of the modulus is probable but not certain.

**Substreams (User Story 11)**

- **FR-054**: The system MUST split a sequence into `k` substreams of length `L`, substream `i` starting at the state reached by jumping `i * L` steps from the seed.
- **FR-055**: Concatenating the substreams in order MUST equal the first `k * L` outputs of the plain sequence.
- **FR-056**: `k * L > m` MUST be rejected with `stream-exceeds-modulus`; non-positive `k` or `L` with `invalid-count`.

### Error Catalogue

The stable error codes are: `invalid-modulus`, `invalid-multiplier`, `invalid-increment`, `invalid-seed`, `invalid-type`, `invalid-count`, `count-exceeds-limit`, `invalid-jump`, `invalid-range`, `range-exceeds-modulus`, `invalid-bins`, `unknown-preset`, `insecure-purpose`, `insufficient-data`, `ambiguous-parameters`, `stream-exceeds-modulus`, `unsupported-combination` and `malformed-request`.

### Key Entities

- **Parameter set**: multiplier, increment and modulus; the unit every operation works on.
- **Seed / State**: the position in a sequence; always between 0 and `m - 1`.
- **Preset**: a named, published parameter set with a description.
- **Verdict**: the validator's result: full-period or not, expected period, violated conditions, per-condition outcomes.
- **Sequence result**: outputs, outputs consumed, next state, warnings and the security marker.
- **Quality report**: the fixed set of metrics for one generator, seed and sample.
- **Prediction**: recovered parameters, predicted values and the insecurity notice.
- **Substream**: a block of outputs with its starting state and index.
- **Error**: code, message and offending field.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of the acceptance criteria of the stories of priority P1 and P2 pass in the harness; the criteria of P3 stories pass if those stories are built.
- **SC-002**: The validator's verdict agrees with the brute-force true period for 100% (0 disagreements) of the 89,439 parameter triples with `2 <= m <= 64`.
- **SC-003**: Jump-ahead equals stepping for 100% of `n` from 0 to 1000 on every preset, and uses at most 64 modular multiplications for any `n < 2^64`.
- **SC-004**: On the shared example set, the library, the command line (JSON) and the HTTP service give identical results in 100% of cases.
- **SC-005**: Repeating any request 100 times gives 100 byte-identical results.
- **SC-006**: 100% of successful results carry the not-secure marker, and 100% of requests with a refused purpose return no values.
- **SC-007**: In the invalid-input test set, 0 inputs cause a crash, a server error or an unstructured error.
- **SC-008**: For every range size from 1 to 16 on the 16-value full-period example, each value in the range occurs exactly the same number of times over one period.
- **SC-009**: Every quality gate in the constitution (Principle II) passes.

## Assumptions

- Users are developers and students who call the library, run the command line or call the HTTP service; there are no accounts, authentication or rate limits. The HTTP service is intended for local and demonstration use, not for exposure to untrusted networks.
- Integers have unlimited precision at the specification level; the 64-bit upper bound on `m` is a deliberate limit, not an accident of implementation.
- The seed is always supplied by the caller; the toolkit has no default seed and never reads the clock or any ambient source.
- Presets are named for their published origin: `glibc-type0` is the simple LCG mode of the GNU C library's random-number routines, not the default `rand()` generator of modern systems.
- Quality thresholds are conventional, not proofs: a sound generator is flagged by chance in about 1% of samples per statistical check, and the same input always gives the same verdict. The checks cannot see every flaw: at 10,000 samples both RANDU and the glibc multiplier with an even increment pass the uniformity and serial-correlation checks, which is why the verdict is worded `no-defect-detected`, not `good`.
- Out of scope: predicting from truncated outputs when the parameters are unknown (needs lattice-reduction methods), cryptographically secure generation, non-LCG generators, statistical test batteries beyond the four listed metrics, persistence, authentication, and distributions other than uniform.
- A preset's published reference values were checked against an independent reference calculation before being written into this specification.
