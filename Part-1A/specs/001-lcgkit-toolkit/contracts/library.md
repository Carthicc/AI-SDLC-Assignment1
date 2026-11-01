# Library contract

Two levels, both importable.

## `lcgkit.ops`: the operations layer

This is what the command line and the HTTP service call. One function per capability, each taking a plain mapping (the request) and returning a plain mapping (the result) or raising `LcgError`. Values are native Python integers here; `lcgkit.wire` converts them to and from decimal strings for JSON.

```python
def run(operation: str, request: Mapping[str, object]) -> dict[str, object]: ...
# operation is one of: "presets", "sequence", "integers", "fractions",
# "jump", "streams", "validate", "quality", "predict"
```

`run` applies the field table (order, types, ranges, the first-error rule), calls the core, adds `cryptographically_secure: false`, and applies the purpose guard last.

## `lcgkit.core`: pure functions

No input checking beyond what the types express, no clock, no randomness, no global state. Callers (the operations layer) have already validated. Each function is small enough to test and to mutate on its own.

| Module | Function | Requirement |
|---|---|---|
| `lcg` | `step(p, x) -> int`, `sequence(p, seed, count) -> SequenceResult` | FR-002, FR-003 |
| `presets` | `PRESETS`, `get(name) -> ParameterSet` | FR-009 to FR-012 |
| `validator` | `validate(p) -> Verdict` | FR-013 to FR-015 |
| `numtheory` | `is_prime(n)`, `factor(n)`, `modinv(a, m)`, `solve_linear(a, b, m)` | FR-014, FR-039 to FR-043 |
| `jump` | `jump(p, state, steps) -> int` | FR-016 to FR-018 |
| `bounded` | `integers(p, seed, lo, hi, count)`, `fractions(p, seed, count)` | FR-019 to FR-022 |
| `quality` | `report(p, seed, sample_size, bins) -> QualityReport` | FR-026 to FR-031 |
| `stats` | `chi_square_p(statistic, dof)`, `serial_correlation(values)` | FR-029, FR-030 |
| `predictor` | `predict_known_modulus`, `predict_unknown_modulus`, `predict_truncated` | FR-039 to FR-045 |
| `streams` | `split(p, seed, streams, length) -> list[Stream]` | FR-046, FR-047 |
| `guard` | `check_purpose(label) -> None` (raises `insecure-purpose`) | FR-023 to FR-025 |

`lcgkit.errors` defines `LcgError(code, message, field)` and the list of the 18 codes.

The core's cost promises: `jump` uses at most 64 modular multiplications for any `steps < 2^64` (FR-018); everything else follows the limits in the data model.
