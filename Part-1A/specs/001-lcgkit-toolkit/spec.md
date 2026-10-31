# Feature Specification: lcgkit — a Linear Congruential Generator Toolkit

**Input**: A small, properly specified toolkit around the linear congruential generator, a simple and very old way of producing repeatable number sequences. It generates sequences from custom or well-known parameters, checks whether a set of parameters is any good, jumps ahead in a sequence, draws fair integers and fractions, refuses security-sensitive uses, reports on sequence quality, and can be used as a library, from the command line, or as a stateless HTTP service. Two stretch features show why an LCG is not secure: a predictor and a stream splitter.

## Terminology

- **Parameter set**: multiplier `a`, increment `c`, modulus `m`.
- **Seed**: the starting state `x0`. It is *not* part of the output.
- **Step**: `x(n+1) = (a·x(n) + c) mod m`. Output `k` is `x(k)`, so the first output is `x(1)`.
- **Next state**: the state after the last output, or the seed if nothing was produced. Using it as the next seed continues the same sequence.
- **Full period**: the sequence visits all `m` values before repeating.
- **Interface**: library, command line, or HTTP service.
- **Decimal string**: an integer written as text: digits only, no spaces, no exponent, no leading zeros (except the single digit `0`), and a minus sign only for range bounds. JSON carries large integers this way because many JSON readers round anything above 2^53.

## Clarifications

- Q: When the command line and the HTTP service send numbers as JSON, should values that can exceed 9 quadrillion travel as ordinary JSON numbers or as text strings? → A: Decimal strings for every field that can exceed 2^53, in and out; counts and bin numbers stay ordinary numbers.
- Q: When a request has more than one mistake, should the system report only the first error it finds, in a fixed order, or all of them? → A: Only the first error, checking fields in a fixed order (`m`, `a`, `c`, seed, then the operation's own fields), one error per response.
- Q: Which operations should accept the purpose label that blocks requests for tokens, keys and passwords: only the ones that return random-looking numbers, or also jump-ahead and stream-splitting? → A: Sequence, integers, fractions, streams and jump-ahead accept it; the validator, quality report and predictor do not.
- Q: Should the spec set a maximum response time for the biggest requests, and if so how strict? → A: Generous limits on a typical laptop: 5 seconds for 1,000,000 generated values, 15 seconds for the largest quality report, 5 seconds for the truncated-output search at 20 hidden bits.
- Q: When someone asks the predictor to predict what comes next but does not say how many values, how many should it return by default? → A: 10; the caller may ask for any number up to the 1,000,000 limit.

## User Scenarios & Testing

Stories are listed in priority order: P1 is the core, P2 builds on it, P3 is stretch. Each can be built and tested on its own. Every acceptance criterion has an ID (`AC-nnn`) that the tasks and tests will cite, together with the requirement it checks.

### User Story 1 — Generate a repeatable sequence (Priority: P1)

A developer hands over a parameter set, a seed and a count and gets back exactly that many numbers. Ask again and the numbers are the same; ask for more, starting where the last answer ended, and the sequence carries on without a gap. Everything else in the toolkit is built on this, so it comes first. It can be checked on its own with the worked example and the list of invalid inputs below.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-001 | Given `a=5, c=3, m=16, seed=7`, when I ask for 5 values, then I get `[6, 1, 8, 11, 10]` and next state `10`. | FR-002, FR-003 |
| AC-002 | Given the result of AC-001, when I ask for 3 more values starting from its next state, then I get `[5, 12, 15]`. Asking for 8 values in one go gives `[6, 1, 8, 11, 10, 5, 12, 15]`. | FR-003 |
| AC-003 | Given any valid input, when the count is 0, then the list is empty and the next state equals the seed. | FR-004 |
| AC-004 | Given a count of exactly 1,000,000, the request succeeds; given 1,000,001 the error is `count-exceeds-limit`; given a negative count the error is `invalid-count`. | FR-004 |
| AC-005 | Given `m=1` or `m=2^64+1`, the error is `invalid-modulus`. Given `m=16` and `a=16`, `invalid-multiplier`; `c=-1`, `invalid-increment`; `seed=16`, `invalid-seed`. No values are returned. | FR-001 |
| AC-006 | Given a numeric field supplied as `3.5`, `"abc"`, `true` or `null`, the error is `invalid-type` and names the field. | FR-001 |
| AC-007 | Given `m=1` and `seed=16` together, the only error is `invalid-modulus`. Given `m=16`, `a=16` and `seed=16`, it is `invalid-multiplier`. Given `m` of the wrong type and a negative count, it is `invalid-type` naming `m`. Every interface reports the same single error. | FR-001, FR-036 |
| AC-008 | Given `a=6364136223846793005, c=1442695040888963407, m=2^64, seed=0`, when I ask for 2 values, then I get `[1442695040888963407, 1876011003808476466]` (no overflow at the 64-bit limit). | FR-002 |
| AC-009 | Given any valid request, when it is sent 100 times, all 100 answers are byte-for-byte identical. | FR-005 |
| AC-010 | Given any successful request, the answer contains `cryptographically_secure: false`. | FR-006 |
| AC-011 | Given a request for 1,000,000 values, the answer arrives within 5 seconds. | FR-008 |
| AC-012 | Given `c=0` and `seed=0`, the outputs are all zero and the answer carries the warning `zero-fixed-point`. Given `a` equal to 0 or 1, it carries `degenerate-multiplier`. | FR-007 |

### User Story 2 — Use well-known generators by name (Priority: P1)

Instead of typing multipliers and moduli, a developer picks a well-known generator by name (the classic minimal standard, the C library ones and so on) and can ask which ones exist. Published generators give the tests outside reference values to compare against, which is why they are in the first group. Check it by requesting each preset with the seed shown below.

| ID | Preset (a, c, m) | Seed | First outputs | Requirement |
|---|---|---|---|---|
| AC-013 | `minstd` (16807, 0, 2^31−1) | 1 | 16807, 282475249, 1622650073, 984943658, 1144108930; the 10,000th output is 1043618065 | FR-009 |
| AC-014 | `minstd-new` (48271, 0, 2^31−1) | 1 | 48271, 182605794, 1291394886; the 10,000th output is 399268537 | FR-009 |
| AC-015 | `glibc-type0` (1103515245, 12345, 2^31) | 1 | 1103527590, 377401575, 662824084 | FR-009 |
| AC-016 | `numrec` (1664525, 1013904223, 2^32) | 0 | 1013904223, 1196435762, 3519870697 | FR-009 |
| AC-017 | `musl` (6364136223846793005, 1, 2^64) | 0 | 1, 6364136223846793006, 13885033948157127959 | FR-009 |
| AC-018 | `pcg-lcg64` (6364136223846793005, 1442695040888963407, 2^64) | 0 | 1442695040888963407, 1876011003808476466 | FR-009 |
| AC-019 | `randu` (65539, 0, 2^31) | 1 | 65539, 393225, 1769499, 7077969 | FR-009 |

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-020 | When I ask for the list of presets, I get exactly the seven above, in that order, each with its `a`, `c`, `m` and a one-line description. | FR-010 |
| AC-021 | Given any preset, asking by name gives the same result as writing its parameters out. | FR-011 |
| AC-022 | Given a name that does not exist, the error is `unknown-preset`. | FR-012 |

### User Story 3 — Find out whether parameters are any good (Priority: P1)

Someone learning about generators submits a parameter set and learns whether it reaches a full period and, if not, which rule it breaks. A good example is the glibc multiplier paired with an even increment: it looks reasonable, but it can never give a full period. This is the easiest part to test honestly, because for small moduli the whole cycle can simply be walked and counted, and that count has to match the verdict.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-023 | Given `a=1103515245, c=24680, m=2^31` (the glibc multiplier with an even increment), the verdict is `not-full-period` with exactly one reason: `increment-not-coprime`. | FR-013, FR-014 |
| AC-024 | Given `glibc-type0`, `numrec`, `musl` or `pcg-lcg64`, the verdict is `full-period`, the expected period equals `m`, and there are no reasons. | FR-013 |
| AC-025 | Given `minstd` (`c=0`), the verdict is `not-full-period` with the reasons `increment-not-coprime` and `multiplier-minus-one-not-divisible-by-prime-factor`, in that order. | FR-014 |
| AC-026 | Given `m=16, a=3, c=1`, the only reason is `multiplier-minus-one-not-divisible-by-four`. Given `m=2, a=1, c=1`, the verdict is `full-period`. | FR-013, FR-014 |
| AC-027 | Given every triple with `2 ≤ m ≤ 64` and `0 ≤ a, c < m` (89,439 of them), the verdict matches the brute-force result (full period exactly when the measured period from seed 0 is `m`), with zero disagreements. | FR-015 |
| AC-028 | Given any valid parameter set, the answer shows pass or fail for each of the three conditions separately. | FR-014 |

### User Story 4 — Jump ahead (Priority: P1)

A developer wants the state after a huge number of steps (a billion, say) without computing every step in between, for example to start parallel workers far apart in one long sequence. It is a classic LCG feature and easy to get subtly wrong, so it belongs in the first group. Check it against plain stepping for small distances and against known identities for enormous ones.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-029 | Given each preset and seed 1, for every `n` from 0 to 1000, the jumped state equals the state reached by stepping `n` times. | FR-016 |
| AC-030 | Given `minstd`, seed 1, `n=10000`, the state is `1043618065`. | FR-016 |
| AC-031 | Given `glibc-type0` and any seed, jumping `2^31` steps (its full period) returns the seed, and jumping `2^31 + 5` equals jumping 5. | FR-016 |
| AC-032 | Jumping `n1` and then `n2` equals jumping `n1 + n2` in one go. | FR-016 |
| AC-033 | `n = 2^64 − 1` works; `n = 2^64` or a negative `n` gives `invalid-jump`. | FR-017 |
| AC-034 | For any `n < 2^64`, the jump uses at most 64 modular multiplications. | FR-018 |

### User Story 5 — Draw fair integers and fractions (Priority: P1)

A developer wants whole numbers inside a range (a die roll, for instance) or fractions between 0 and 1, and does not want any value favoured. Two traps are well known: rounding a scaled value makes the two end values half as likely as the rest, and taking a remainder leans on the weakest, lowest bits of a power-of-two modulus. The checks use a tiny generator where every value can be counted over one full cycle.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-035 | Given `a=5, c=3, m=16, seed=7` and the range 1 to 3, when exactly one full period (16 outputs) is used, then 1, 2 and 3 each appear exactly 5 times, one output was discarded, and the answer reports 16 outputs consumed. | FR-019, FR-021 |
| AC-036 | Given the same generator and any range size from 1 to 16, every value in the range appears the same number of times over one full period. | FR-019 |
| AC-037 | Given the range −3 to 3, every value is inside it. | FR-019 |
| AC-038 | Given a range with one value (`lo = hi`), that value is returned every time, no output is consumed and the state does not change. | FR-020 |
| AC-039 | Given `lo > hi` the error is `invalid-range`; given a range with more values than `m`, `range-exceeds-modulus`; given non-integer bounds, `invalid-type`. | FR-020 |
| AC-040 | Given `glibc-type0`, seed 1, range 0 to 1, the first 64 values do not strictly alternate (the weak low bit must not decide the result). | FR-019 |
| AC-041 | Drawing 10 values in one request equals drawing 4 and then 6 from the reported next state. | FR-021 |
| AC-042 | Given `a=5, c=3, m=16, seed=7`, 5 fractions come back as `[0.375, 0.0625, 0.5, 0.6875, 0.625]`. | FR-022 |
| AC-043 | Given the `pcg-lcg64` parameters and seed `15635871386175874928` (whose next output is `m−1`), the fraction is strictly less than 1.0. | FR-022 |

### User Story 6 — Refuse security-sensitive uses (Priority: P2)

Anyone who says the numbers are for a token, key or password is turned down and pointed to a cryptographically secure source, because an LCG is predictable. The label can be given to every operation that hands out numbers or states: sequences, integers, fractions, streams and jump-ahead. The constitution requires this refusal (Principle V). Check it by sending a mix of purpose labels.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-044 | Given a purpose of `token`, `Session Token`, `KEYS` or `api-key`, the request fails with `insecure-purpose`, no values come back, and the message points to a cryptographically secure source. | FR-023, FR-024 |
| AC-045 | Given `dice`, `monkey business`, `simulation` or no purpose at all, the request goes through (matching is by whole word, so `monkey` is not `key`). | FR-024 |
| AC-046 | Each of `token`, `key`, `password`, `secret`, `session`, `nonce`, `salt`, `credential`, `otp`, in singular and plural, is refused. | FR-024 |
| AC-047 | Given a purpose of `password` sent to a jump-ahead request and to a stream-splitting request, each fails with `insecure-purpose` and returns no state or values. The validator, quality report and predictor take no purpose label. | FR-023, FR-024 |
| AC-048 | The documentation says the guard relies on the declared purpose and cannot catch misuse that is not declared. | FR-025 |

### User Story 7 — Report on sequence quality (Priority: P2)

A learner asks for a short, fixed set of measurements on a generator's output to see why one parameter set is better than another: how long before it repeats, how evenly it spreads values, whether neighbouring values are related, and how the low bits behave. It turns the theory behind the validator into numbers. It is checked with tiny generators where every number can be worked out by hand.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-049 | Given `a=5, c=3, m=16, seed=7`, sample 16, 16 bins: period 16, chi-square exactly 0, the uniformity and independence checks are `not-applicable`, the period check passes and the verdict is `caution`. | FR-026, FR-029 |
| AC-050 | Given `a=1, c=0, m=16, seed=3`, sample 16, 16 bins: period 1, chi-square exactly 240, the period check fails and the verdict is `defect-detected`. | FR-026, FR-029 |
| AC-051 | Given a constant sequence, the serial correlation is reported as `undefined`, never as a not-a-number or a crash. | FR-026 |
| AC-052 | Given `glibc-type0`, seed 1, the lowest bit has period 2, the lowest two bits 4 and the lowest three bits 8. | FR-026 |
| AC-053 | Given a modulus that is not a power of two (such as `minstd`), the low-bit periods are `not-applicable`. Given `m` above 2^24, the measured period is `not-computed` and the other numbers still appear. | FR-026 |
| AC-054 | Given a sample size of exactly 1,000,000 the report succeeds; 1,000,001 gives `count-exceeds-limit`; a sample below 2 gives `invalid-count`; fewer than 1 bin or more bins than the sample gives `invalid-bins`. | FR-028 |
| AC-055 | Repeating any quality request gives identical numbers, and they match an independent reference calculation to a relative tolerance of 1e-9. | FR-027 |
| AC-056 | Given a quality report with sample size 1,000,000 and `m = 2^24`, the answer arrives within 15 seconds. | FR-008 |
| AC-057 | Given `minstd`, seed 1, sample 10,000, 10 bins: chi-square 6.69, p-value 0.6694, serial correlation −0.0005 (to the digits shown), every check passes, verdict `no-defect-detected`. | FR-029 |
| AC-058 | Given `glibc-type0`, seed 1, sample 10,000, 10 bins: chi-square 8.882, p-value 0.4482, serial correlation −0.00111, no check fails, the low-bits flag `low-bits-short-period` is raised, verdict `caution`. | FR-029 |
| AC-059 | The p-value for the published 1% critical values 6.635 (1 degree of freedom), 9.210 (2), 23.209 (10) and 135.807 (100) is 0.01 within 0.0005. | FR-030 |
| AC-060 | Every report states that passing the checks does not show a generator is random or secure. | FR-031 |

### User Story 8 — Use it from the command line (Priority: P2)

A user runs the toolkit in a terminal and gets readable output by default, JSON when they want to feed it to a script, and exit statuses a script can rely on. It is the quickest way to show the toolkit working. Check it by running the worked examples and looking at the output, the exit status and which stream the text goes to.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-061 | Every capability in stories 1 to 7, 10 and 11 can be run from the command line. | FR-032 |
| AC-062 | With the structured-output option the output parses as JSON and equals the library's result for the same input. | FR-033 |
| AC-063 | With the structured-output option, every field that can exceed 2^53 is written as a decimal string, and counts and bin numbers are written as numbers. | FR-033 |
| AC-064 | Without that option the output is readable text containing the same values. | FR-033 |
| AC-065 | Success exits with 0. Invalid input exits with a non-zero status, and a refused purpose with a different non-zero status. Errors go to the error stream and nothing goes to the result stream. | FR-034 |

### User Story 9 — Use it as an HTTP service (Priority: P2)

A client application calls the toolkit over HTTP. Each request carries everything it needs, so the service stores nothing and any instance can answer any request, and a published description of the interface matches what the service really does. This is the basis of the contract-test gate in the constitution. Check it by sending the shared examples and running contract checks against that description.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-066 | Every capability in stories 1 to 7, 10 and 11 is available as a request/response operation. A follow-up request that uses a returned next state matches one longer request. | FR-035 |
| AC-067 | Two identical requests get byte-for-byte identical response bodies. | FR-035, FR-005 |
| AC-068 | Given the `pcg-lcg64` parameters and seed 0 sent as decimal strings, asking for 2 values returns `["1442695040888963407", "1876011003808476466"]`. | FR-035 |
| AC-069 | Given a large field (`a`, `c`, `m`, seed, state, jump distance or range bound) sent as a JSON number, or as a string that is not a decimal string (`"0x10"`, `"1e3"`, `"007"`, `" 5"`), the error is `invalid-type` and names the field; the value is never rounded. | FR-035 |
| AC-070 | Invalid input gets a client-error status with the structured error body; a refused purpose gets a different client-error status. | FR-036 |
| AC-071 | Malformed JSON, missing or unknown fields, wrong types, oversized numbers and empty bodies all get a structured client error (`malformed-request` or the specific code), never a server error. | FR-036 |
| AC-072 | Generated contract tests find no mismatch between the published interface description and the actual behaviour. | FR-037 |
| AC-073 | On the shared example set, the service's results equal the library's. | FR-038 |

### User Story 10 — Predict a sequence from what you have seen (Priority: P3)

A learner gives the toolkit some outputs they have seen and watches it work out what comes next, which shows concretely why an LCG must never protect a secret. Three situations are covered: (A) the modulus is known and the outputs are complete; (B) the modulus is unknown and the outputs are complete; (C) the parameters are known but each output is cut down to its high bits, as some C libraries do. It is the riskiest story, and the toolkit is complete without it, so it can be dropped without touching the rest. Check it by generating outputs from a known preset, hiding what the predictor should not know, and comparing its predictions with the real continuation.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-074 | (A) Given `m=2^31` and the first 5 outputs of `glibc-type0` from seed 1, the recovered parameters are `a=1103515245, c=12345` and the next 10 predictions equal the real next 10 outputs. | FR-039, FR-042 |
| AC-075 | Given a prediction request that does not give `k`, 10 values are returned; given `k=3`, 3 values; given `k=1,000,001`, the error is `count-exceeds-limit`; given `k=0`, `invalid-count`. | FR-045 |
| AC-076 | (A) Given only 2 outputs, the error is `insufficient-data`. Given `m=16` and the outputs `[0, 0, 0]`, where many multipliers fit, the error is `ambiguous-parameters` and no guess is returned. | FR-043 |
| AC-077 | (B) Given no modulus and the first 12 outputs of `glibc-type0` from seed 1, the recovered modulus is `2^31`, the parameters are `1103515245` and `12345`, and the next 10 predictions are correct. The same holds for `pcg-lcg64` from seed 0, with modulus `2^64`. | FR-040, FR-042 |
| AC-078 | (B) Given no modulus and fewer than 12 outputs, the error is `insufficient-data`. | FR-040, FR-043 |
| AC-079 | (C) Given `glibc-type0` (parameters known), 16 hidden low bits, and the first 4 outputs of seed 1 shifted right by 16 (15 visible bits each), the full internal state is recovered and the next 10 full-width outputs are predicted correctly. | FR-041, FR-042 |
| AC-080 | (C) Given the same setting but only 2 truncated outputs, two states fit, so the error is `ambiguous-parameters`. | FR-041, FR-043 |
| AC-081 | (C) Given truncated outputs with unknown parameters, or more than 20 hidden bits (for example `musl`, which returns 31 of 64 bits and hides 33), or a modulus that is not a power of two, the error is `unsupported-combination`. | FR-041 |
| AC-082 | (C) Given `glibc-type0`-style outputs with exactly 20 hidden bits, the truncated-output search finishes within 5 seconds. | FR-008 |
| AC-083 | Every successful prediction says it shows the generator is insecure. Case (B) also says that recovering the modulus is probable, not certain. | FR-044 |

### User Story 11 — Split a sequence into separate streams (Priority: P3)

A developer cuts one sequence into separate blocks, one per worker, so that parallel workers never reuse the same numbers. It shows off jump-ahead, but nothing else needs it. Check it by joining the streams and comparing the result with the plain sequence.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-084 | Given `glibc-type0`, seed 1, 4 streams of length 5, joining the streams in order gives the first 20 outputs of the plain sequence. | FR-046 |
| AC-085 | In the same request, the start of stream `i` (from 0) equals the jump-ahead state at `i × 5`. | FR-046 |
| AC-086 | When streams times length exceeds `m`, the error is `stream-exceeds-modulus`; a zero or negative stream count or length gives `invalid-count`. | FR-047 |

### Edge Cases

- The smallest (`m = 2`) and largest (`m = 2^64`) moduli are accepted; `m = 1`, `m = 2^64 + 1` and negatives are not.
- A generator stuck at zero (`c = 0`, `seed = 0`) is accepted with a warning, not rejected.
- A count of 0 returns an empty list.
- Very large integers, decimals, strings, booleans and `null` in a numeric field give a structured error, never a crash.
- For a 64-bit modulus, dividing the largest output by `m` rounds to exactly 1.0 in ordinary floating point (AC-043).
- Power-of-two moduli have weak low bits, so ranges must not simply take a remainder (AC-040).
- A request with several mistakes gets one error, the first in the fixed checking order, and every interface reports the same one.
- A purpose label with extra spaces, capitals or punctuation is cleaned up before matching.
- In JSON, a plain number where a decimal string is required (for example `m` sent as a number) is rejected, never silently rounded.
- A legitimate answer can be large: 1,000,000 values of 64-bit size is roughly 20 MB of text.

## Requirements

### Functional Requirements

**Generation**

- **FR-001**: The system shall accept only integer inputs with `2 ≤ m ≤ 2^64`, `0 ≤ a < m`, `0 ≤ c < m` and `0 ≤ seed < m`. Otherwise it shall return no values and a single error with a stable code, a message and the name of the offending field. When several inputs are invalid, only the first error is reported, checking in this order: `m`, `a`, `c`, seed, then the operation's own inputs in the order the interface description lists them; for one field, a wrong type is reported before a wrong value.
- **FR-002**: The system shall produce outputs by `x(n+1) = (a·x(n) + c) mod m`, exactly, for every accepted `m`, and shall not include the seed in the output.
- **FR-003**: The system shall report the next state with every generation result.
- **FR-004**: The system shall accept a count `n` with `0 ≤ n ≤ 1,000,000`. The same limit applies to every operation that produces or consumes a list: sample size, streams times length, outputs given to the predictor, and predicted values. A count of 0 gives an empty list and an unchanged state.
- **FR-005**: Identical input shall give byte-identical output on every run of the same interface. Across interfaces the content is equal, as the command-line and HTTP requirements state.
- **FR-006**: Every successful result shall carry `cryptographically_secure: false`.
- **FR-007**: The system shall accept degenerate settings and flag them with a warning: `zero-fixed-point` (`c = 0` and `seed = 0`) and `degenerate-multiplier` (`a` is 0 or 1).
- **FR-008**: On a typical laptop, the largest generation request (1,000,000 values) shall finish within 5 seconds, the largest quality report (sample size 1,000,000, `m = 2^24`) within 15 seconds, and the truncated-output search at 20 hidden bits within 5 seconds. These are safety limits set well above the measured times, to catch a slow implementation without failing at random.

**Presets**

- **FR-009**: The system shall provide these presets, with the parameters in AC-013 to AC-019: `minstd` (Park–Miller minimal standard), `minstd-new` (revised multiplier), `glibc-type0` (the simple mode of the GNU C library), `numrec` (Numerical Recipes' quick generator), `musl` (the musl C library's `rand`), `pcg-lcg64` (the 64-bit LCG used by the PCG family) and `randu` (IBM's RANDU, included as a known-bad example).
- **FR-010**: The system shall list the presets with their parameters and a one-line description.
- **FR-011**: A request using a preset name shall give the same result as one using that preset's written-out parameters.
- **FR-012**: When the preset name is unknown, the system shall reject the request with `unknown-preset`.

**Parameter validation**

- **FR-013**: For any valid parameter set the system shall give a verdict of `full-period` or `not-full-period`, and for `full-period` also the expected period (equal to `m`).
- **FR-014**: The system shall report the outcome of each of the three Hull–Dobell conditions, and for `not-full-period` list every broken one, always in this order: `increment-not-coprime`, `multiplier-minus-one-not-divisible-by-prime-factor`, `multiplier-minus-one-not-divisible-by-four`. The conditions are: `c` is coprime with `m`; `a − 1` is divisible by every prime factor of `m`; `a − 1` is divisible by 4 when `m` is.
- **FR-015**: The verdict shall agree with the true period of the sequence for every parameter set (SC-002).

**Jump-ahead**

- **FR-016**: The system shall return the state after `n` steps from a given state, for `0 ≤ n < 2^64`, equal to the state reached by stepping `n` times.
- **FR-017**: When `n` is outside that range, the system shall reject it with `invalid-jump`.
- **FR-018**: As constitution Principle IV requires, a jump shall use at most 64 modular multiplications for any `n < 2^64`.

**Bounded integers and fractions**

- **FR-019**: The system shall draw integers from an inclusive range `[lo, hi]`, negative bounds allowed. Over one full period of a full-period generator, every value in the range shall occur equally often. The system shall discard outputs that would cause bias, shall base the result on the high-order part of the output, and shall not use rounding or a plain remainder.
- **FR-020**: When `lo > hi` the system shall reject the request with `invalid-range`; when the range has more values than `m`, with `range-exceeds-modulus`. A range with one value returns that value, uses no output and leaves the state unchanged.
- **FR-021**: Results shall report how many outputs were consumed and the next state, so that splitting a request gives the same values as one request.
- **FR-022**: The system shall produce fractions in `[0, 1)` as output divided by `m`, and a result shall never equal 1.0, even for a 64-bit modulus.

**Misuse guard**

- **FR-023**: The sequence, integer, fraction, stream and jump-ahead operations shall each accept an optional `purpose` label. The validator, the quality report and the predictor return no usable numbers and do not take one.
- **FR-024**: The system shall clean the label (trim, lower-case, split on anything that is not a letter or digit). If any word of the label is `token`, `key`, `password`, `secret`, `session`, `nonce`, `salt`, `credential` or `otp`, or a plural of these, the request shall fail with `insecure-purpose`, return no values and recommend a cryptographically secure source. Any other label, or none, is accepted.
- **FR-025**: The documentation shall state that the guard depends on the declared purpose and cannot detect undeclared misuse.

**Quality report**

- **FR-026**: Given a parameter set, seed, sample size `N` and bin count, the system shall report: the measured period (when `m ≤ 2^24`, otherwise `not-computed`); the chi-square statistic over equal-width bins and its p-value; the lag-1 serial correlation (`undefined` for a constant sequence); the periods of the lowest 1, 2 and 3 bits (when `m` is a power of two, otherwise `not-applicable`); and the overall verdict (FR-029).
- **FR-027**: Quality numbers shall be repeatable and shall match an independent reference calculation to a relative tolerance of 1e-9.
- **FR-028**: The system shall accept a sample size from 2 to 1,000,000 and a bin count from 1 to the sample size, and otherwise reject with `invalid-count`, `count-exceeds-limit` or `invalid-bins`.
- **FR-029**: The system shall report each check below with its value and an outcome of `pass`, `fail` or `not-applicable`:
  - *period-covers-sample*: the measured period is at least the sample size (not applicable when the period is `not-computed`);
  - *uniformity*: the chi-square p-value is at least 0.01 (not applicable when sample size divided by bin count is below 10);
  - *independence*: the absolute lag-1 serial correlation is at most `2.576 / √N` (not applicable when `N` is below 100);
  - *low-bits*: flagged `low-bits-short-period` when `m` is a power of two; informational, never a failure.

  The verdict is `defect-detected` if any applicable check fails, otherwise `caution` if the low-bits flag is raised, otherwise `no-defect-detected`. These thresholds are fixed by this specification and change only through a documented amendment.
- **FR-030**: The p-value shall be the upper-tail probability of the chi-square distribution with `bins − 1` degrees of freedom, and shall match the published 1% critical values (AC-059).
- **FR-031**: Every report shall say that passing does not show randomness or security. The documentation shall give the source of each threshold in `references.md`, and record as decisions anything with no source: the minimum sample of 100 for the independence check, the period check, the three verdict levels and the single-sample judgement.

**Command line**

- **FR-032**: Every capability shall be usable from the command line.
- **FR-033**: Output shall be readable text by default and JSON on request, and the JSON shall equal the library's result. In JSON, every integer field that can exceed 2^53 (`a`, `c`, `m`, seeds, states, outputs, predicted values, jump distances and range bounds) is a decimal string, on input and on output; counts and bin numbers are ordinary JSON numbers.
- **FR-034**: The exit status shall be 0 on success and non-zero on failure, with different statuses for invalid input and a refused purpose. Results go to standard output and errors to standard error.

**HTTP service**

- **FR-035**: Every capability shall be available as a stateless request/response operation. The service shall store nothing, and continuing a sequence uses the returned next state. JSON integers follow the rule in FR-033: a JSON number, or a string that is not a decimal string, in a field that must be a decimal string is rejected with `invalid-type` and never rounded.
- **FR-036**: Invalid input shall get a client-error status with the structured error body (one error, chosen by the order in FR-001), and a refused purpose a different client-error status. No input, however malformed, shall cause a server error; unreadable requests get `malformed-request`.
- **FR-037**: A machine-readable description of the interface shall be published and shall match the behaviour.
- **FR-038**: Results shall equal the library's results for the same input.

**Predictor**

- **FR-039** (case A): Given a known modulus and at least 3 consecutive complete outputs, the system shall recover the multiplier and increment when they are uniquely determined, and predict the next `k` values.
- **FR-040** (case B): Given no modulus and at least 12 consecutive complete outputs, the system shall recover the modulus (a value larger than every output), then the multiplier and increment, and predict the next `k` values.
- **FR-041** (case C): Given known parameters, a power-of-two modulus, at most 20 hidden low-order bits and truncated outputs, the system shall recover the full internal state and predict the next `k` full-width values. Truncated outputs with unknown parameters are out of scope and are rejected with `unsupported-combination`, as are more than 20 hidden bits and a modulus that is not a power of two.
- **FR-042**: The recovered parameters or state shall reproduce every output that was supplied.
- **FR-043**: With too few outputs the system shall answer `insufficient-data`; when several solutions fit equally well, `ambiguous-parameters` with no guess.
- **FR-044**: Every prediction shall say it shows the generator is insecure; case B shall add that recovering the modulus is probable, not certain.
- **FR-045**: The number of values to predict, `k`, shall default to 10 when the caller gives none. The caller may set it from 1 to 1,000,000; a `k` above the limit gets `count-exceeds-limit` and a `k` below 1 gets `invalid-count`.

**Streams**

- **FR-046**: The system shall split a sequence into `k` streams of length `L`, stream `i` starting at the state reached by jumping `i × L` steps from the seed. Joined in order, they shall equal the first `k × L` outputs of the plain sequence.
- **FR-047**: When `k × L > m` the system shall reject the request with `stream-exceeds-modulus`; a non-positive `k` or `L` gets `invalid-count`.

### Error codes

`invalid-modulus`, `invalid-multiplier`, `invalid-increment`, `invalid-seed`, `invalid-type`, `invalid-count`, `count-exceeds-limit`, `invalid-jump`, `invalid-range`, `range-exceeds-modulus`, `invalid-bins`, `unknown-preset`, `insecure-purpose`, `insufficient-data`, `ambiguous-parameters`, `stream-exceeds-modulus`, `unsupported-combination`, `malformed-request`.

### Key Entities

- **Parameter set** and **seed/state**: what every operation works on; the state is always between 0 and `m − 1`.
- **Preset**: a named parameter set with a one-line description.
- **Verdict**: the validator's result (full period or not, reasons, per-condition outcomes).
- **Sequence result**: outputs, outputs consumed, next state, warnings and the security marker.
- **Quality report**, **Prediction**, **Stream**, **Error**: the results of stories 7, 10, 11 and of any failure.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All acceptance criteria of the P1 and P2 stories pass in the harness; the P3 criteria pass if those stories are built.
- **SC-002**: The validator agrees with the brute-force period on all 89,439 triples with `2 ≤ m ≤ 64` (zero disagreements).
- **SC-003**: Jump-ahead equals stepping for every `n` from 0 to 1000 on every preset, and never uses more than 64 modular multiplications for `n < 2^64`.
- **SC-004**: On the shared example set, the library, the command line (JSON) and the HTTP service give identical results in every case.
- **SC-005**: Repeating any request 100 times on the same interface gives 100 byte-identical answers.
- **SC-006**: Every successful answer carries the not-secure marker, and every request with a refused purpose returns no values.
- **SC-007**: In the invalid-input test set, no input causes a crash, a server error or an unstructured error.
- **SC-008**: For every range size from 1 to 16 on the 16-value full-period example, each value in the range occurs exactly equally often over one period.
- **SC-009**: Every quality gate in the constitution (Principle II) passes.
- **SC-010**: The three largest requests (1,000,000 values; the largest quality report; the 20-bit search) finish within the limits in FR-008.

## Assumptions

- Users are developers and students. There are no accounts, authentication or rate limits, so the HTTP service is for local and demonstration use, not for untrusted networks.
- The modulus limit of 2^64 is a deliberate choice. The seed is always supplied by the caller; the toolkit never reads the clock or any other ambient source.
- Presets are named after where their parameters are published; the sources and what could and could not be verified are in `references.md`. In particular, Knuth's *TAOCP* Vol. 2 credits the multiplier `6364136223846793005` to C. E. Haynes and gives no increment, so `musl` (increment 1, from the musl source) and `pcg-lcg64` (increment `1442695040888963407`, from the PCG reference code) are named after those code bases and not after Knuth.
- `glibc-type0` is the simple LCG mode of the GNU C library's random routines, not the default `rand()` of modern systems.
- The quality checks are conventional, not proofs. A sound generator is flagged by chance in about 1% of samples per statistical check, and the same input always gives the same verdict. They cannot see every flaw: at 10,000 samples both RANDU and the glibc multiplier with an even increment pass the uniformity and serial-correlation checks, which is why the verdict is worded `no-defect-detected` and never "good". The verdict also judges one sample, where NIST SP 800-22 tests many.
- Reference values in this specification were calculated with independent throwaway scripts before being written down; the 10,000th `minstd` outputs also match the published Park–Miller check values.
- The time limits in FR-008 are safety nets, set between 5 and 50 times above the measured times (about 0.11 s for 1,000,000 values, 1 s for the largest period measurement and 0.2 s for the 20-bit search in plain Python). They are measured on the machine that runs the harness and are not to be tightened or loosened to suit a result.
- The limit of 20 hidden bits for truncated outputs (FR-041) comes from measurement. The search takes about 0.2 seconds at 20 bits and its cost doubles with every extra bit (3.3 s at 24, 58 s at 28; a 33-bit case such as `musl` would take an estimated half hour in Python). Keeping it at 20 keeps every request, and every automated test, fast.
- Out of scope: predicting from truncated outputs when the parameters are unknown (this needs lattice-reduction methods), cryptographically secure generation, non-LCG generators, more statistical tests than the ones listed, persistence, authentication, and distributions other than uniform.
