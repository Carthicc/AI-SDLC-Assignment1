# Research: lcgkit

Each entry gives the decision, the reason, and what else was considered. Measurements were taken on my personal laptop (macOS, Python 3.12); the throwaway scripts that produced them are not part of the repository.

## R1. Language and tooling

- **Decision**: Python 3.12 managed with uv, as the constitution requires (Principle VII, Technology constraints).
- **Reason**: measured in plain Python 3.12, the heaviest requests in the spec are fast: 1,000,000 values in 0.11 s, JSON text for them in 0.05 s, the period of an `m = 2^24` generator in 0.96 s, the 20-hidden-bit search in 0.21 s, and the brute-force check of all 89,439 small parameter sets in 0.09 s. FR-008's limits (5 s, 15 s, 5 s) are far above these.
- **Alternatives**: Rust or Go would be faster, but nothing here needs it, and the constitution's gates (Ruff, mypy, Bandit, pytest, mutation testing) are all Python tools. Switching would need a constitutional amendment and a new harness.

## R2. Command line: argparse, not Typer

- **Decision**: the command line uses `argparse` from the standard library.
- **Reason**: Principle VII says standard library first and no dependency without a plan justification. Eleven small subcommands do not need Typer or Click.
- **Alternatives**: Typer (nicer help text, but adds Click and a typing layer), Click.

## R3. HTTP service: FastAPI and uvicorn, with our own request parsing

- **Decision**: FastAPI served by uvicorn. Each route reads the raw JSON body and hands it to the shared operations layer; it does not use Pydantic request models for validation. Pydantic is used only to describe response bodies in the OpenAPI document.
- **Reason**: FR-001 requires one error per request, chosen by a fixed field order (`m`, `a`, `c`, seed, then the operation's own fields, type before value for each field). Pydantic checks all types before any value rule, so it cannot produce that order, and its default 422 body is not our error shape. One validator shared by the library, command line and service is also what keeps the three interfaces identical (FR-038, SC-004). FastAPI still earns its place by generating the OpenAPI description (FR-037) that the contract tests read.
- **Alternatives**: `http.server` from the standard library (no OpenAPI, we would hand-write routing), Flask (needs an extension for OpenAPI), Starlette alone (no OpenAPI generation).

## R4. One operations layer behind every interface

- **Decision**: `lcgkit.ops` exposes one function per capability. It takes a plain request mapping, validates it with the field table in `lcgkit.fields`, calls the pure code in `lcgkit.core`, and returns a plain result mapping. The command line and the service are thin adapters over it.
- **Reason**: FR-005, FR-038 and SC-004 demand identical results from all three interfaces. Having one code path makes that true by construction and makes the parity tests simple.
- **Alternatives**: separate validation per interface (three places to drift apart).

## R5. Large integers in JSON

- **Decision**: a small `lcgkit.wire` module converts between decimal strings and Python integers for the fields marked "large" in the field table. Counts and bin numbers stay ordinary numbers. The same field table feeds the OpenAPI schemas, so the contract and the code cannot disagree.
- **Reason**: the clarification on decimal strings (FR-033, FR-035); Python integers are unbounded, so nothing else is needed internally.

## R6. Factoring any modulus up to 2^64

- **Decision**: a deterministic Miller–Rabin test (the first twelve primes as bases, which is proven sufficient below 3.3 × 10^24) plus Pollard–Brent rho, both in the standard library.
- **Reason**: the validator needs the prime factors of `m` for every `m` up to 2^64 (FR-013 and FR-014, the Hull–Dobell conditions). Measured on the hardest case, products of two random 32-bit primes: worst of 20 runs 44 ms; `2^64` is instant.
- **Alternatives**: trial division (too slow for a 64-bit semiprime), sympy as a dependency (a large package for one function, against Principle VII). Tests use a trial-division oracle for moduli up to 10^12, known factorisations for the large ones, and the brute-force period check for every `m ≤ 64`.

## R7. Chi-square p-value

- **Decision**: the regularised upper incomplete gamma function, computed with a power series for small arguments and a continued fraction for large ones, using `math.lgamma`.
- **Reason**: this is the same function NIST SP 800-22 uses for its p-values (`igamc`, section 2.2.4). It reproduces the published 1% critical values at 1, 2, 3, 10 and 100 degrees of freedom (6.635, 9.210, 11.345, 23.209, 135.807), which is acceptance criterion AC-059.
- **Alternatives**: SciPy (a heavy dependency for one function).

## R8. Fractions never reach 1.0

- **Decision**: compute `output / m` and, if the result is 1.0 or more, return `math.nextafter(1.0, 0.0)`.
- **Reason**: measured: `(2^64 − 1) / 2^64` evaluates to exactly `1.0` in ordinary floating point (`0.9999999999999999` is the largest double below 1). FR-022 and AC-043 require a result strictly below 1.0.

## R9. Fair integers in a range

- **Decision**: with `size = hi − lo + 1` and `q = m // size`, accept an output `v` only if `v < size × q`, and return `lo + v // q`; otherwise discard it and take the next output.
- **Reason**: every value in the range then occurs exactly `q` times in a full period (FR-019, SC-008), the result depends on the high-order part of `v` so a weak low bit cannot decide it (AC-040), and no rounding or plain remainder is used. A hand check on `a=5, c=3, m=16, seed=7`, range 1 to 3, gives 5 of each value and one discarded output, as AC-035 states.

## R10. Measuring the period

- **Decision**: Brent's cycle detection (constant memory), used only when `m ≤ 2^24` (FR-026).
- **Reason**: 16.7 million steps in 0.96 s; the answer is the length of the cycle the seed ends up in, which equals the brute-force count used as the test oracle.

## R11. Predictor

- **Decision**: case A solves `a·(x2 − x1) ≡ x3 − x2 (mod m)` with a modular inverse and enumerates all solutions when the difference is not invertible (more than one solution means `ambiguous-parameters`). Case B takes the gcd of the determinants `t(n+2)·t(n) − t(n+1)²` of consecutive differences, then runs case A with that modulus; at least 12 outputs, as measured (with 6 to 8 outputs one 64-bit generator returned a multiple of the true modulus). Case C tries every hidden value for the first output and keeps those that reproduce the following truncated outputs.
- **Reason**: all measured. Case C costs 0.01 s at 16 hidden bits, 0.20 s at 20, 3.3 s at 24 and 58 s at 28, which is why the limit stays at 20. The number of truncated outputs needed grows as the visible bits shrink (4 outputs at 16 hidden bits, 12 at 28).

## R12. Test strategy

- **Decision**: pytest for tests, Hypothesis for property tests, pytest-cov for branch coverage. Tests carry markers `ac("AC-nnn")` and `fr("FR-nnn")`. A separate package `tests/oracle/` holds independent reference calculations (naive stepping, brute-force period, trial-division factoring, published values); tests never import the implementation to compute an expected value.
- **Reason**: Principle III (independent oracles, tests derived from AC IDs) and Principle VI (traceability). The harness checks that every acceptance criterion in the spec has at least one marked test.
- **Alternatives**: unittest (no parametrisation, no plugins), tests that call the implementation to produce expected values (circular).

Hypothesis runs with a registered profile that sets `derandomize=True` and a fixed number of examples, so the same checks give the same result on every run.

## R13. Contract tests

- **Decision**: Schemathesis (4.32.7) reads the OpenAPI document that the service generates and calls the service in process.
- **Reason**: Principle II lists OpenAPI contract tests as a gate; FR-037 asks for the description to match the behaviour; SC-007 and FR-036 ask that no input causes a server error, which Schemathesis's generated bad inputs probe directly.

## R14. Mutation testing

- **Decision**: mutmut 3.8.1, run against `src/lcgkit/core/` only, with the threshold from the constitution (85%).
- **Reason**: smoke-tested here on a small project: 13 of 13 mutants killed in 9 s (93 mutations per second), so the tool works on this machine. In mutmut 3.x the config keys `paths_to_mutate` and `tests_dir` are deprecated; the plan uses `source_paths` and `pytest_add_cli_args_test_selection`.
- **Scope**: the timing tests are excluded from mutation runs (`-m "not perf"`), since they say nothing about correctness and are slow.
- **Risk kept open**: the real project will have thousands of mutants and slower tests. If the run time becomes unmanageable, the constitution's governance applies (a recorded amendment, not a silent drop).

## R15. Function length and docstrings

- **Decision**: Ruff has a statement-count rule (`PLR0915`) but no "lines per function" rule, so the harness includes a small AST check that fails any function longer than 40 lines. For "documented" in Principle II, the Ruff rule set gains the `D1` rules (missing docstring) for public items.
- **Reason**: the constitution says "functions at most 40 lines" and "all public functions fully typed and documented". Adding `D1` makes the second sentence enforceable; it makes the bar stricter, not lower. Recorded as amendment v1.0.1.

## R16. Secret scanning and dependency audit

- **Decision**: gitleaks and pip-audit both run in the harness. gitleaks was installed with `brew install gitleaks`. pip-audit queries an online vulnerability database, so it needs network access.
- **Reason**: Principle II. A gate that cannot run reports FAIL, never a silent skip.

## R17. Anti-tampering

- **Decision**: before implementation starts, I tag the repository (`baseline-before-implement`). The harness fails if any protected path differs from that tag: `tests/`, `specs/`, `.specify/memory/constitution.md`, `.harness/` and the tool configuration in `pyproject.toml`; the one exception is `specs/001-lcgkit-toolkit/tasks.md`, which may differ from the tag only in its checkboxes because the implementation ticks tasks off. It also fails on fewer test functions than the tag records (`test_functions=<N>`, counted statically with `ast`, because the tests cannot be collected while `src/` is still empty), on new `skip`, `xfail`, `noqa`, `nosec` or `type: ignore` markers, and on any use of the standard-library `random` module under `src/`.
- **Reason**: Principle III. Comparing against a Git tag is harder for an agent to quietly change than a hash file stored in the working tree. A legitimate change to a protected file goes through the Spec Kit artifacts, a new commit and a new tag made by me.

## R18. Logging

- **Decision**: the HTTP service logs one line per request with the method, path and status, and never the body (seeds and outputs stay out of logs). Results never depend on the clock; any timestamp comes from the logging formatter, outside the computation.
- **Reason**: closes the observability gap left open after the clarification stage. Principle IV forbids wall-clock use in computation; logging is operational. Principle IV was clarified to say so (amendment v1.0.1).

## R19. HTTP status codes and routes

- **Decision**: `200` success, `400` any invalid or malformed input, `403` for a refused purpose (`insecure-purpose`), unknown routes and methods also `400` with the same error body and code `malformed-request`. Routes are `POST /v1/sequence`, `/v1/integers`, `/v1/fractions`, `/v1/jump`, `/v1/streams`, `/v1/validate`, `/v1/quality`, `/v1/predict`, and `GET /v1/presets`. An unexpected exception returns `500` with `internal-error`; reaching it counts as a defect.
- **Reason**: FR-036 needs two different client-error statuses for invalid input and for a refusal; the `/v1` prefix leaves room to change the contract later.

## R20. Naming the jump distance

- **Decision**: in requests, the jump distance is called `steps`; `count` always means "how many values". The specification used `n` for both.
- **Reason**: removes the ambiguity noted at the end of the clarification stage without touching the spec's IDs.

## R21. Cost of a jump

- **Decision**: double the affine map once per bit of `steps`: from `(A, C)` form `(A·A, C·(A + 1))`, two multiplications, and apply `x → A·x + C` for every set bit, one multiplication. At most three per bit, so at most 190 for 64 bits; the bound in the specification is 192. All multiplications go through one function, `mulmod(x, y, m)` in `core/jump.py`, so a test can count them.
- **Reason**: the bound of 64 in the first version of the specification cannot be met by any algorithm. Each multiplication at most doubles an exponent, so reaching `a^n` for `n = 2^64 − 1` takes at least 64 multiplications for `a^n` alone, and more because `n` has 64 set bits; the increment part adds to that. The constitution was amended to 192 (v1.0.2). The requirement is still logarithmic in `n`, so a step-by-step loop still fails it. This is an argument, not a measurement.

## Dependencies (Principle VII)

| Package | Version tested | Used for | Why not the standard library |
|---|---|---|---|
| fastapi (brings pydantic, starlette) | 0.162.0 | HTTP routing and OpenAPI generation | no OpenAPI support in the standard library |
| uvicorn | 0.54.0 | serving the app | an ASGI server is needed |
| pytest, pytest-cov | 9.2.0, 7.1.0 | tests and branch coverage | unittest lacks parametrisation and markers |
| hypothesis | 6.170.14 | property tests | no equivalent |
| httpx | 0.28.1 | in-process HTTP client for tests | required by the FastAPI test client |
| schemathesis | 4.32.7 | OpenAPI contract tests | Principle II gate |
| pyyaml | 6.x (arrives with schemathesis) | the contract test reads `contracts/openapi.yaml` | no YAML parser in the standard library |
| mutmut | 3.8.1 | mutation score | Principle II gate |
| ruff, mypy, bandit, pip-audit | 0.17.3, 2.4.1, 1.9.4, 2.10.1 | lint, types, security, dependency audit | Principle II gates |

Only fastapi and uvicorn are runtime dependencies; everything else is development-only. gitleaks is a separate binary, not a Python package.
