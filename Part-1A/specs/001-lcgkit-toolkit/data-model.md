# Data Model: lcgkit

Nothing is stored. Every request carries all its inputs and every answer carries everything needed to continue (FR-035). This document describes the shapes that pass through the system and the rules that govern them.

## Field table

The field table is the single source of truth for validation order, wire types, error codes and the OpenAPI schemas. In JSON, a field marked *large* is a decimal string (digits only, no sign, no leading zeros, no spaces or exponent; a leading minus only for `lo` and `hi`). Fields marked *count* are ordinary JSON numbers.

Fields are checked in the order shown. For each field the type is checked first, then the value. Only the first error is reported (FR-001). An operation's own fields follow `m`, `a`, `c` and `seed`.

| Field | Wire type | Rule | Error code | Requirement |
|---|---|---|---|---|
| `preset` | string | one of the seven names; replaces `a`, `c`, `m`; sending it together with any of them is a `malformed-request` | `unknown-preset` | FR-009 to FR-012 |
| `m` | large | integer, 2 ≤ m ≤ 2^64 | `invalid-modulus` | FR-001 |
| `a` | large | integer, 0 ≤ a < m | `invalid-multiplier` | FR-001 |
| `c` | large | integer, 0 ≤ c < m | `invalid-increment` | FR-001 |
| `seed` | large | integer, 0 ≤ seed < m | `invalid-seed` | FR-001 |
| `state` (jump only) | large | integer, 0 ≤ state < m | `invalid-seed` | FR-016 |
| `count` | count | integer, 0 ≤ count ≤ 1,000,000 | `invalid-count`, `count-exceeds-limit` | FR-004 |
| `lo`, `hi` | large (signed) | integers, lo ≤ hi, hi − lo + 1 ≤ m | `invalid-range`, `range-exceeds-modulus` | FR-019, FR-020 |
| `steps` (jump only) | large | integer, 0 ≤ steps < 2^64 | `invalid-jump` | FR-016, FR-017 |
| `sample_size` | count | integer, 2 ≤ sample_size ≤ 1,000,000 | `invalid-count`, `count-exceeds-limit` | FR-028 |
| `bins` | count | integer, 1 ≤ bins ≤ sample_size | `invalid-bins` | FR-028 |
| `outputs` (predict) | list of large | 1 to 1,000,000 values | `insufficient-data`, `count-exceeds-limit` | FR-039, FR-040, FR-043 |
| `hidden_bits` (predict) | count | integer ≥ 0 | `unsupported-combination` | FR-041 |
| `k` (predict) | count | integer, default 10, 1 ≤ k ≤ 1,000,000 | `invalid-count`, `count-exceeds-limit` | FR-045 |
| `streams`, `length` | count | each ≥ 1; `streams × length` ≤ m | `invalid-count`, `stream-exceeds-modulus` | FR-046, FR-047 |
| `purpose` | string | optional label; checked last, after every other field is valid | `insecure-purpose` | FR-023, FR-024 |

Checking order for each operation: `preset` (or `m`, `a`, `c`), then `seed` (or `state`), then the operation's own fields in this order.

| Operation | Own fields, in checking order | Accepts `purpose` |
|---|---|---|
| sequence | `count` | yes |
| integers | `lo`, `hi`, `count` | yes |
| fractions | `count` | yes |
| jump | `state`, `steps` | yes |
| streams | `streams`, `length` | yes |
| validate | none (no `seed`) | no |
| quality | `sample_size`, `bins` | no |
| predict | `outputs`, `m`, `a`, `c`, `hidden_bits`, `k` | no |
| presets | none | no |

For `predict`, `a` and `c` are accepted only together with `m` and a positive `hidden_bits` (case C); otherwise the request is a `malformed-request` naming that field.

A wrong type for any field gives `invalid-type` naming that field. A body that is not a JSON object, has an unknown field, or cannot be read gives `malformed-request`.

## Entities

All entities are immutable dataclasses in `lcgkit.core`, built from plain integers. They never contain wire strings; `lcgkit.wire` converts them.

### ParameterSet
`a`, `c`, `m` (integers). Valid when the rules above hold. A *preset* is a named ParameterSet with a one-line description. There are seven: `minstd`, `minstd-new`, `glibc-type0`, `numrec`, `musl`, `pcg-lcg64`, `randu`, with the parameters in the specification (AC-013 to AC-019).

### SequenceResult
`outputs` (list of integers), `outputs_consumed` (integer), `next_state` (integer), `warnings` (list of codes: `zero-fixed-point`, `degenerate-multiplier`). For integer draws, `values` replaces `outputs`; `outputs_consumed` can exceed the number of values because biased outputs are discarded (FR-019, FR-021).

### Verdict (validator)
`verdict` (`full-period` or `not-full-period`), `expected_period` (equal to `m`, present only for `full-period`), `conditions` (the three Hull–Dobell conditions, each with `name` and `passed`), `reasons` (the names of the failed conditions in the fixed order `increment-not-coprime`, `multiplier-minus-one-not-divisible-by-prime-factor`, `multiplier-minus-one-not-divisible-by-four`).

### QualityReport
`measured_period` (integer, or `not-computed` when `m > 2^24`), `chi_square` (number), `p_value` (number), `serial_correlation` (number, or `undefined` for a constant sequence), `low_bit_periods` (periods of the lowest 1, 2 and 3 bits, or `not-applicable` when `m` is not a power of two), `checks` (a list of `{name, value, outcome}` for *period-covers-sample*, *uniformity*, *independence* and *low-bits*, each outcome `pass`, `fail` or `not-applicable`), `verdict` (`defect-detected`, `caution` or `no-defect-detected`) and `notice` (the statement that passing proves nothing, FR-031). Thresholds are constants: p ≥ 0.01, |r| ≤ 2.576/√N for N ≥ 100, at least 10 expected values per bin (FR-029).

### Prediction
`case` (`A`, `B` or `C`), `modulus` (case B), `a`, `c` (cases A and B), `state` (case C), `predictions` (the next `k` values), `notice` (the statement that this shows the generator is insecure; case B adds that recovering the modulus is probable, not certain, FR-044).

### Stream
`index`, `start_state`, `outputs`; a streams answer is a list of these (FR-046).

### LcgError
`code` (one of the 18 stable codes in the specification), `message` (plain text), `field` (the offending field, when there is one). Raised inside the code as an exception, returned as `{"error": {"code", "message", "field"}}` by the interfaces.

## Common to every successful answer

`cryptographically_secure: false` is added to every successful result (FR-006). `warnings` is present on the generating operations. `next_state` is present wherever a sequence can be continued.

## State and lifecycle

There is none. A generator's state is a single integer between 0 and `m − 1`; stepping it is the only transition, `x → (a·x + c) mod m`, and the interfaces hand it back to the caller as `next_state`.

## Size limits

Any list of values, in a request or an answer, has at most 1,000,000 entries (FR-004). Truncated-output prediction supports at most 20 hidden bits (FR-041). A fair-integer draw that discards more than 1,000,000 outputs in a row ends with `unsupported-combination` naming `seed` (FR-048).
