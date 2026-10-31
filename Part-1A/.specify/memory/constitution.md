# lcgkit Constitution
lcgkit is a deterministic Linear Congruential Generator toolkit: a library, a CLI and a
stateless HTTP API.

## Core Principles

### I. Specification Is Authoritative
Code MUST follow the approved specification, plan and tasks. No implementation MAY begin
before the specification is approved. An ambiguity found later MUST be resolved by amending
the upstream Spec Kit artifact with a recorded change; it MUST NOT be patched around in code.

### II. Quality Gates (NON-NEGOTIABLE)
One harness runner MUST execute every gate below, print an unambiguous PASS or FAIL, and
write machine-readable results. Every gate MUST pass:
- Ruff with rule sets E, F, I, B, UP, S, C90, PL, RUF: zero errors; cyclomatic complexity
  at most 8; functions at most 40 lines.
- mypy --strict: zero errors; all public functions fully typed and documented.
- Bandit: zero findings of medium severity or above.
- pip-audit: zero known vulnerabilities. gitleaks: zero findings.
- Tests: all pass; branch coverage at least 95%; mutation score at least 85% on the core
  module.
- OpenAPI contract tests pass against the HTTP API.

### III. Test Integrity
Tests MUST derive from acceptance-criterion IDs (AC-xxx) in the specification. The following
are forbidden: deleting, skipping or xfail-ing tests; lowering assertions or thresholds;
adding noqa, nosec or type-ignore suppressions; editing tests, the specification or harness
configuration in order to obtain a pass. The harness MUST hash-check protected files and
enforce a minimum test count. Tests MUST use independent oracles and never the implementation
under test.

### IV. Determinism
Identical input MUST give byte-identical output. Code MUST NOT use wall-clock time, ambient
randomness or global state. The standard-library `random` module MUST NOT be used in `src/`.
Jump-ahead MUST use at most 64 modular multiplications for any n below 2^64.

### V. Honest Security Posture
An LCG is NOT cryptographically secure and the project MUST NOT claim otherwise. Requests
for tokens, keys or passwords MUST be refused. Secrets, keys and `.env` files MUST NEVER be
committed.

### VI. Traceability
Every task MUST cite specification IDs. Every test and every public function MUST cite its AC
or task ID. There MUST be one commit per Spec-Driven-Development stage. The first AI
generation MUST be preserved unchanged before any repair.

### VII. Simplicity
Python 3.12 standard library comes first. Dependencies MUST be limited to those justified in
the plan, and none MAY be added without a plan amendment.

## Technology & Security Constraints
- Language and tooling: Python 3.12 managed with uv.
- Layout: application code in `src/`, specification-derived tests in `tests/`, harness gates
  and runner in `.harness/`, evidence in `evidence/`.
- Protected paths (agent MUST NOT modify to obtain a pass): `tests/`, the specification
  artifacts, `.harness/` configuration and this constitution.
- The API is stateless: all inputs arrive in the request and nothing is persisted.

## Development Workflow
- Stage order: constitution, specify, clarify, plan, tasks, analyze, implement, harness,
  repair, revalidate, human ACCEPT/REJECT.
- Harness failures MUST be fixed in the implementation, never by weakening the specification
  or the harness. A legitimate specification change MUST go through the Spec Kit artifacts
  and be documented.
- A human MUST record the final ACCEPT or REJECT decision, with known limitations, after the
  automated harness result.

## Governance
This constitution supersedes all other practices for this project. Amendments MUST be
documented with a rationale, a version bump and the date, and MUST NOT lower a quality gate
without a recorded justification. Versioning follows semantic versioning: MAJOR for
backward-incompatible principle removals or redefinitions, MINOR for a new principle or
materially expanded guidance, PATCH for clarifications. Compliance MUST be checked at the
plan, analyze and harness stages.

**Version**: 1.0.0 | **Ratified**: 2026-11-01 | **Last Amended**: 2026-11-01
