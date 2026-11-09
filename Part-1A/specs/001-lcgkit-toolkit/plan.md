# Implementation Plan: lcgkit

Input: the specification in `spec.md` (48 requirements, 90 acceptance criteria, 10 success criteria, 5 recorded clarifications) and the constitution in `.specify/memory/constitution.md` (v1.0.3).

## Summary

lcgkit is one small core of pure number-crunching functions with three thin ways in: a Python library, a command line and a stateless HTTP service. All three go through one operations layer that validates a request with a single field table, so they cannot disagree on validation, error order or results. The core uses only the standard library. FastAPI and uvicorn serve the HTTP interface; everything else added is development tooling for the quality gates in the constitution.

The harness is built before the implementation and lives outside the code it checks. It runs eleven gates (lint, function length, types, security, secrets, dependency audit, tests with branch coverage, mutation testing, contract tests, integrity and traceability), writes machine-readable results and a failure report for each failed gate, and ends with a single PASS or FAIL.

The measurements behind these choices are in `research.md`.

## Technical Context

**Language/Version**: Python 3.12, managed with uv (`requires-python = ">=3.12,<3.13"`, `uv.lock` committed)

**Primary Dependencies**: standard library for all computation; runtime: fastapi 0.162, uvicorn 0.54. Development: pytest, pytest-cov, hypothesis, httpx, schemathesis, mutmut, ruff, mypy, bandit, pip-audit (versions in `research.md`). gitleaks as a separate binary.

**Storage**: none; the service is stateless (FR-035)

**Testing**: pytest with Hypothesis property tests, an independent oracle package, Schemathesis contract tests and mutmut mutation tests

**Target Platform**: macOS and Linux, local and demonstration use (no authentication, spec assumption)

**Project Type**: library with a command line and a web service

**Performance Goals**: FR-008 safety limits on the machine that runs the harness: 1,000,000 values in 5 s, the largest quality report in 15 s, the 20-bit hidden search in 5 s. Measured in plain Python so far: 0.11 s for 1,000,000 values, 0.96 s for the period part of the largest quality report (the rest of that report is not yet measured), 0.2 s for the 20-bit search.

**Constraints**: the quality gates of constitution Principle II; no `random`, clock or global state in computation (Principle IV); at most 192 modular multiplications for any jump (FR-018); ordinary JSON numbers never carry values above 2^53 (FR-033, FR-035)

**Scale/Scope**: nine operations, about eleven modules in the core, an estimated 1,500 lines of source

## Constitution Check

Checked before research and again after design, against constitution v1.0.3. Every row passes.

| Principle | How the plan satisfies it | Status |
|---|---|---|
| I. Specification is authoritative | Plan derives from `spec.md` and every contract cites requirement IDs. Three details the spec leaves open are decided in the data model: a request that gives a preset and explicit parameters is a `malformed-request`; the purpose check comes last, after all inputs are valid; a bad jump state reports `invalid-seed`. The analyze stage should confirm none of them contradicts the spec | Pass |
| II. Quality gates | One gate per item: Ruff (rule set, complexity ≤ 8), a function-length check (≤ 40 lines), mypy --strict, Bandit, pip-audit, gitleaks, pytest with 95% branch coverage, mutmut at 85% on `core/`, Schemathesis contract tests; one runner | Pass, with notes below |
| III. Test integrity | Tests are written from the acceptance criteria before implementation, use an independent oracle, and are protected by comparison with a Git tag; skip, xfail, noqa, nosec and type-ignore are detected | Pass |
| IV. Determinism | The core is pure; the jump is by repeated squaring of the affine map; no clock, `random` or global state in computation | Pass, with a note on logging |
| V. Honest security posture | `guard` refuses insecure purposes; every success carries `cryptographically_secure: false`; the predictor shows the weakness; `.gitignore` and gitleaks keep secrets out | Pass |
| VI. Traceability | Tests carry `ac` and `fr` markers; a traceability gate fails if any acceptance criterion has no test; commits cite IDs; the first generation is committed unchanged before any repair | Pass |
| VII. Simplicity | Standard library first; argparse over Typer; only fastapi and uvicorn at runtime; each dependency justified in `research.md` | Pass |
| Layout | `src/`, `tests/`, `.harness/`, `evidence/` as the constitution lists | Pass |
| Workflow | Plan, then tasks, analyze, harness, implement, repair, human decision | Pass |

Decisions made at this stage (none was a violation; each was a reading of, or an addition to, the constitution):

1. **Docstring rule.** Principle II requires public functions to be "documented". The Ruff `D1` rules (missing docstring) were added to the Ruff set so the harness can check it. Recorded as the patch amendment v1.0.1; it makes the bar stricter.
2. **Logging and Principle IV.** The service logs method, path and status, never bodies, and a log line carries a timestamp from the logging system. The time limits in FR-008 also need timing tests. Principle IV was therefore clarified in v1.0.1: it covers computation and results, and allows measuring time in tests and operational logging.
3. **gitleaks** is installed with Homebrew. It also scans commit history. A gate that cannot run counts as FAIL, and the README will say how to install it.
4. **Mutation testing** keeps the 85% threshold. It was smoke-tested only; if the real run proves unreachable or too slow, the governance rule applies: a recorded amendment backed by evidence, never a silent change.

## Project Structure

### Documentation (this feature)

```text
specs/001-lcgkit-toolkit/
├── spec.md
├── plan.md              # this file
├── research.md          # measurements and decisions
├── data-model.md        # field table, entities, error order
├── quickstart.md        # end-to-end checks
├── references.md        # sources for thresholds and presets
├── checklists/
│   └── requirements.md
└── contracts/
    ├── openapi.yaml     # the HTTP service
    ├── cli.md           # the command line
    └── library.md       # the operations layer and the core
```

### Source code (inside `Part-1A/`)

```text
pyproject.toml           # dependencies, tool configuration
uv.lock
src/lcgkit/
├── __init__.py
├── errors.py            # LcgError, the 18 codes
├── fields.py            # the field table: names, kinds, order, error codes
├── wire.py              # decimal-string conversion for JSON
├── ops.py               # one function per capability; validation, guard, shaping
├── cli.py               # argparse adapter
├── service.py           # FastAPI adapter; OpenAPI generated from fields.py
└── core/                # pure functions, mutated and tested hardest
    ├── lcg.py           # step, sequence
    ├── presets.py
    ├── numtheory.py     # primality, factoring, modular inverse
    ├── validator.py     # Hull–Dobell conditions
    ├── jump.py
    ├── bounded.py       # fair integers, fractions
    ├── stats.py         # chi-square p-value, serial correlation
    ├── quality.py       # period, checks, verdict
    ├── predictor.py     # cases A, B, C
    ├── streams.py
    └── guard.py         # purpose label

tests/
├── oracle/              # independent reference calculations; imports nothing from src/
├── unit/                # one file per core module, derived from the criteria
├── property/            # Hypothesis properties (jump equals stepping, parity, determinism)
├── integration/         # operations layer, CLI, parity across interfaces
├── contract/            # Schemathesis against the generated OpenAPI
└── perf/                # the FR-008 time limits

.harness/
├── run_harness.py       # the single runner: PASS or FAIL, exit status, results.json
├── gates/               # lint, length, types, security, secrets, audit, tests, mutation, contract, integrity, traceability
└── config/              # gitleaks configuration (Ruff, mypy, Bandit and mutmut are configured in pyproject.toml)

evidence/
├── initial-generation/  # first generated source, committed unchanged before any repair
├── final-generation/
├── harness-results/     # one folder per run
└── harness-log.md       # written by me
```

**Structure decision**: a single project with a pure core and thin adapters. The core is the only mutation target and the only place the numbers are computed, which keeps the 85% mutation threshold meaningful.

## Design decisions in brief

The reasons and measurements are in `research.md`; the numbers are in the spec.

- **One request path.** `ops.run(operation, request)` validates with the field table, calls the core and shapes the answer. CLI and HTTP are adapters. Parity (FR-038, SC-004) follows from this.
- **First error only.** The field table fixes the checking order, so one bad request always gets the same error from every interface (FR-001, FR-036).
- **Decimal strings at the edge.** Only `wire.py` knows about decimal strings. The core and the operations layer use plain integers.
- **Fair integers and fractions.** Discard-and-retry on the high-order part of the output; fractions clamped just below 1.0 (research R8, R9).
- **Validator.** Hull–Dobell conditions with deterministic Miller–Rabin and Pollard–Brent factoring.
- **Quality.** Period by Brent cycle detection when `m ≤ 2^24`; p-value from the regularised incomplete gamma function; thresholds fixed as in the spec.
- **Predictor.** Three algorithms, one per case; ambiguity is detected, never guessed.

## Harness design

The harness is written and approved before `/speckit-implement` and does not import the code it checks. Each gate runs as its own subprocess, so a failure in one cannot hide another.

| Gate | Tool | Fails when |
|---|---|---|
| lint | Ruff (E, F, I, B, UP, S, C90, PL, RUF, D1) | any finding; complexity above 8 |
| length | AST check in `.harness/gates/length.py` | a function longer than 40 lines |
| types | mypy --strict | any error |
| security | Bandit | any finding of medium severity or above |
| secrets | gitleaks | any finding |
| audit | pip-audit | any known vulnerability, or the audit cannot run |
| tests | pytest, pytest-cov | any failure; branch coverage below 95%; test count below the baseline |
| mutation | mutmut on `src/lcgkit/core/` | mutation score below 85% |
| contract | Schemathesis on the generated OpenAPI | any mismatch or server error |
| integrity | comparison with the Git tag `baseline-before-implement`; marker scan; `random` scan | a protected path changed (`tasks.md` may change only its checkboxes), fewer test functions than the tag records (counted statically), a new skip, xfail, noqa, nosec or type-ignore, or `random` imported in `src/` |
| traceability | scan of `ac` markers against the spec | an acceptance criterion with no test |

Feedback capture (spec requirement from the assignment, section 3.5): for each failed gate the runner stores the command, exit status, full standard output and error, the failing rule or test, the expected and observed behaviour where the tool reports them, and the requirement and criterion IDs involved, in `feedback.json` next to `results.json`. The coding agent receives that file during repair.

## Complexity Tracking

No constitution violations. The four decisions above are recorded so the analyze stage can check them. The amendments so far (v1.0.1 to v1.0.3) only add, correct or clarify; no gate was lowered.
