# Implementation Plan: lcgkit-assistant

Input: the specification in `spec.md` (26 requirements, 61 acceptance criteria, 6 structural invariants, 9 behavioural properties, 9 success criteria, 9 recorded clarifications) and the constitution in `.specify/memory/constitution.md` (v1.0.0).

## Summary

lcgkit-assistant is a small command-line program with one job: take a sentence, ask Google Gemini what the sentence means, check the model's reply against a fixed contract, and, if the reply is a valid request, run it through lcgkit. The model decides; lcgkit calculates; plain Python checks the reply in between. Nothing is stored.

The harness is built before the application and lives outside it. One runner first checks the application code (lint, security scan, tests, secret scan, protected files) and only then spends model calls: it runs every dataset case three times through the application's command line, checks each answer with three layers written from the specification (structure, properties, comparison with ground truth), computes the scores, and decides PASS or FAIL against the threshold declared in the specification. The model never grades the model.

The measurements and trial calls behind these choices are in `research.md`.

## Technical Context

**Language/Version**: Python 3.12, managed with uv (`requires-python = ">=3.12,<3.13"`, `uv.lock` committed)

**Primary Dependencies**: standard library for the model call (`urllib`), the command line (`argparse`), JSON and hashing; runtime: `lcgkit` from Part 1A, as a local editable path dependency. Development: pytest, ruff, bandit (versions in `research.md`). gitleaks as a separate binary.

**Storage**: none; every request stands alone (spec assumption). Evaluation output is written to files under `evidence/`.

**Testing**: pytest for the deterministic parts, using a fake model service (FR-029); the dataset evaluation for the model's behaviour.

**Target Platform**: macOS and Linux, run from the command line.

**Project Type**: command-line application with an evaluation harness.

**Performance Goals**: SC-008, the complete evaluation finishes in under 15 minutes. 48 cases, 46 of which call the model, × 3 repetitions = 138 calls at roughly 1 second each, plus a 3-second pause between calls, is about 10 minutes.

**Constraints**: the constitution's principles; temperature 0; key only from `GEMINI_API_KEY`; synthetic inputs only; the free tier's request limits are unpublished, so the runner paces its calls.

**Scale/Scope**: nine operations, about six small modules in the application, a dataset of 48 cases, an estimated 600 lines of application code and 900 lines of harness code.

## Constitution Check

Checked before research and again after design, against constitution v1.0.0. Every row passes.

| Principle | How the plan satisfies it | Status |
|---|---|---|
| I. Specification is authoritative | Plan derives from `spec.md`; every contract cites requirement IDs. Spec gaps found while planning (the `--info` option, how criteria that no request text can test are covered) were fixed in the specification first, as visible commits | Pass |
| II. Non-determinism is made testable | Contract in `contracts/reply.schema.json`; INV-01 to INV-06 become the layer 1 checks, PROP-01 to PROP-09 the layer 2 checks; nothing compares exact wording | Pass |
| III. One harness, three layers | `.harness/run_eval.py` is the single runner; layers in separate modules; no model is used as a judge | Pass |
| IV. Threshold declared before evaluation | The threshold is in the specification (FR-025) and the runner reads it from `.harness/threshold.json`, which the baseline tag protects | Pass |
| V. Dataset and guardrail integrity | `evals/dataset.json`, the harness and the tests are protected by comparison with the baseline tag; the tag annotation records the test and dataset counts | Pass |
| VI. Honest evidence | Only the runner writes `evidence/eval-results.json` and the run folders; the model name, settings and prompt hash come from `lcgkit-assistant --info`; an unreachable model fails the case | Pass |
| VII. Safe by design | The system prompt treats request text as data; the key is read from the environment and never printed; the marker phrase and key value are searched for in every answer | Pass |
| VIII. Traceability and simplicity | Tasks cite IDs; cases cite IDs in `covers`; the only added dependency is lcgkit | Pass |
| Layout | `src/`, `prompts/`, `tests/`, `evals/`, `.harness/`, `evidence/` as the constitution lists | Pass |
| Workflow | Constitution, specify, clarify, plan, tasks, analyze, implement, evaluate, repair, re-evaluate, human decision | Pass |

Decisions made at this stage (none was a violation; each was a reading of, or an addition to, the constitution):

1. **Layer 1 is written twice on purpose.** The application checks a reply against the contract before running anything (FR-012), and the harness checks it again with its own code. The harness must not import the application (constitution, technology constraints), and a validator copied from the application would approve the application's own mistakes. Both are written from the specification and lcgkit's field table.
2. **The integrity check joins the pre-checks.** FR-030 lists lint, security, tests and secrets; Principle V also requires the comparison with the baseline tag, so the runner runs it in the same step, before any model call.
3. **Ruff runs without its cache.** In Part 1A a cached lint result hid a real finding until a fresh clone was checked. The gate uses `--no-cache` from the start, and `known-first-party` is set in `pyproject.toml` so the import order does not depend on which files exist.
4. **Results are kept per run.** Each run writes a folder under `evidence/eval-runs/`, and the runner copies the latest results to `evidence/eval-results.json`, so the history of failed and repaired runs is preserved.

## Project Structure

### Documentation (this feature)

```text
specs/001-lcgkit-assistant/
├── spec.md
├── plan.md              # this file
├── research.md          # measurements and decisions
├── data-model.md        # replies, answers, cases, results
├── quickstart.md        # end-to-end checks
├── checklists/
│   └── requirements.md
└── contracts/
    ├── reply.schema.json          # the reply contract (layer 1)
    ├── answer.schema.json         # what the command line prints
    ├── dataset-case.schema.json   # one evaluation case, and the dataset file
    ├── eval-results.schema.json   # what the runner writes
    └── cli.md                     # the command line
```

### Source code (inside `Part-1B/`)

```text
pyproject.toml           # dependencies, tool configuration, console script
uv.lock
prompts/
└── system.md            # the system prompt, including the marker phrase
src/lcgkit_assistant/
├── __init__.py
├── config.py            # model name, limits, timeouts, error codes (named constants)
├── contract.py          # checks a reply against the contract (FR-012)
├── model.py             # Gemini call: request, retries, parsing (FR-014)
├── assistant.py         # the rules and the flow for one request text
└── cli.py               # argparse adapter, --info, exit codes (FR-013)

tests/
├── conftest.py          # markers ac/fr/prop/inv, fake model service
├── unit/                # rules, contract, model client, assistant, cli (fake service)
└── harness/             # scoring, layers and runner, with hand-made answers

evals/
└── dataset.json         # the cases, with ground truth and covers

.harness/
├── run_eval.py          # the single runner
├── threshold.json       # the declared threshold and the scoring weights
├── prechecks.py         # lint, security, tests, secrets, integrity (before any model call)
├── dataset.py           # loads the dataset, checks traceability (FR-028)
├── layers/
│   ├── structure.py     # layer 1
│   ├── properties.py    # layer 2
│   └── semantic.py      # layer 3
├── scoring.py           # repetition and case scores, aggregation, verdict
├── report.py            # results and feedback files
├── app.py               # runs the application's command line as a subprocess
└── selfcheck.py         # shows each layer can fail, using fake applications

evidence/
├── initial-generation/  # first generated src/ and prompts/, committed unchanged before any repair
├── final-generation/
├── eval-runs/           # one folder per run: eval-results.json, feedback.json
├── eval-results.json    # copy of the latest run
└── harness-log.md       # written by me
```

**Structure decision**: a small application with the model call isolated in one module, so everything else can be tested without the network, and a harness that reaches the application only through its command line. The harness uses lcgkit (Part 1A) as the independent validator of what a valid request is.

## Design decisions in brief

The reasons and measurements are in `research.md`.

- **One request path.** `assistant.handle(text)` applies the emptiness and length rules, checks the key, calls the model once (with bounded retries for rate limits and server errors), parses and checks the reply, and runs lcgkit for a `call`. The command line only prints the answer.
- **The model decides, the code checks.** The Gemini response schema nudges the model towards the contract; it does not guarantee it, so the application and the harness both check.
- **No judge.** Layer 3 is an exact comparison with the case's ground truth.
- **Pacing.** The application makes one request per run; the runner waits between runs (3 seconds by default) so the free tier's unpublished limit is not hit, and the application retries only when the service says to slow down.
- **Honest failure.** A reply that breaks the contract is `invalid-reply`, with no second try (clarification 3); an unreachable service is `model-unavailable`; both fail their case.

## Harness design

| Step | What it does | Fails when |
|---|---|---|
| 1. Pre-checks | Ruff (without cache), Bandit, pytest, gitleaks, and the integrity check against the Git tag `baseline-before-implement` | any finding or failure; a protected path differs from the tag; fewer tests or dataset cases than the tag records; a new skip, xfail, noqa, nosec or type-ignore. No model call is made |
| 2. Dataset check | Loads `evals/dataset.json` and checks traceability (FR-028): every AC, INV and PROP has a case or a `covered_elsewhere` entry; no unknown IDs; at least 30 cases; the category, operation and guardrail minimums (FR-020) | any rule is broken |
| 3. Evaluation | Runs every case three times through the command line, pausing between runs; applies layers 1, 2 and 3 to each repetition | an unreachable service (the case fails); never skipped |
| 4. Scoring | Repetition scores, case scores, the six metrics, the verdict (FR-024 to FR-026) | overall score below 0.85, a guardrail case below 1.0, or any layer 1 failure |
| 5. Output | Writes `evidence/eval-runs/<run-id>/eval-results.json` and, on failure, `feedback.json`; copies the results to `evidence/eval-results.json`; prints PASS or FAIL | none (exit status 0 only on PASS) |

Feedback capture: for each failed case the runner stores the case, the answer, the failed layer or property, and the expected and observed values (FR-027), in plain text that can be handed to the coding agent unchanged.

## Complexity Tracking

No constitution violations. The four decisions above are recorded so the analyze stage can check them. The harness is larger than the application on purpose: the assignment weighs the evaluation, and the application is deliberately small.
