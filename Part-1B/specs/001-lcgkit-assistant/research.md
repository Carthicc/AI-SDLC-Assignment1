# Research: lcgkit-assistant

Decisions, the alternatives considered, and the measurements behind them. The trial calls were made with a throwaway prompt and are not evaluation evidence; none of their output was saved.

## R1. How to call the model

- **Decision**: call the Gemini REST endpoint `https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent` with the standard library (`urllib.request`), sending the key in the `x-goog-api-key` header, never in the URL.
- **Reason**: one request and one JSON response is all the application needs. Using the standard library keeps the dependency list to lcgkit alone (constitution, Principle VIII) and keeps the fake model service for tests trivial: it replaces one function.
- **Alternatives**: the official Google client library (a large extra dependency for one call); a generic HTTP library such as `httpx` (also an extra dependency).

## R2. Structured output

- **Decision**: ask for JSON with `responseMimeType: application/json` and a flat `responseSchema` (an object whose only required field is `decision`, an enum of the three decisions; the other fields optional). The strict contract is enforced by code, not by the schema.
- **Reason**: Gemini's response schema is a subset of JSON Schema and does not express "exactly these fields for each decision". A flat schema worked in trial calls (six of six replies were valid JSON that followed it). Because the schema only guides the model, layer 1 and the application's own check (FR-012) remain necessary.
- **Alternatives**: no schema (more free-form replies, more `reply-not-json`); a schema with `anyOf` per decision (not relied on, since support varies by model).

## R3. Which model

- **Decision**: `gemini-3.5-flash-lite`, recorded by `lcgkit-assistant --info`.
- **Measured**: with a one-line prompt, `gemini-3.5-flash-lite` answered in 1.3 seconds and `gemini-3.8-flash` took 340 seconds for the same request. Six sequential calls to the lite model took between 0.8 and 1.2 seconds each, with no rate-limit error and the same reply for three identical requests at temperature 0.
- **Reason**: an evaluation of about 114 calls is only practical with a fast model. Both models are on the free tier. `gemini-2.5-flash` is avoided because the provider has announced it will be rerouted to a different model on 1 December 2026, which would change results.

## R4. Pacing, timeouts and retries

- **Decision**: the application times a call out after 60 seconds and retries at most three times, only for HTTP 429 and 5xx responses, waiting for the `Retry-After` header when present and otherwise 5, 15 and 45 seconds. The runner pauses 3 seconds between runs that called the model (a `--min-interval` option).
- **Reason**: the free tier's request limits are not published on the pricing or rate-limit pages; they vary by model and project and can be read in the provider's console. With about 1 second per call plus a 3-second pause the rate stays at about 15 requests per minute, which should be inside any free-tier limit for a lite model. If the console shows a lower limit, the interval is raised without any change to the specification.
- **Alternatives**: no pacing (risks a rate-limit storm and wasted retries); a retry on a bad reply (rejected in the clarifications, because it hides layer 1 failures).

## R5. The system prompt

- **Decision**: a single file `prompts/system.md` with: the role; the nine operations and the mandatory values of each; the rules of FR-003 to FR-011 in plain words; the output format; and a marker phrase that the model must never repeat. `--info` reports the SHA-256 of the file.
- **Rules for writing it**: it contains no request text from the dataset (so the evaluation cannot be passed by memorising examples), and examples in it use made-up numbers that no case uses.
- **Reason**: the prompt is part of the implementation, so the repair step may change it; the dataset and harness may not.

## R6. lcgkit as a dependency and as the validator

- **Decision**: `lcgkit = { path = "../Part-1A", editable = true }` under `[tool.uv.sources]`. The application runs requests with `lcgkit.ops.run` after `lcgkit.wire.decode_request`. The harness uses `lcgkit.fields.OPERATIONS`, `lcgkit.fields.FIELDS` and `lcgkit.wire` to decide whether a field is allowed and of the right kind.
- **Checked**: in a scratch project, `uv sync` installed lcgkit from the local folder, `lcgkit.fields.OPERATIONS` listed all nine operations, and a `sequence` request for minstd, seed 42, count 5 returned `[705894, 1126542223, 1579310009, 565444343, 807934826]`.
- **Reason**: lcgkit's field table is already the single source of truth for what a valid request is, and it was verified in Part 1A, independently of this application.

## R7. How the harness reaches the application

- **Decision**: the runner starts the application as a subprocess, `python -m lcgkit_assistant.cli "<text>"`, and reads the JSON answer from standard output. It never imports `lcgkit_assistant`. An `--app` option replaces the command, which is how the self-check and the tests of the harness supply fake applications.
- **Reason**: the constitution forbids the harness from importing what it evaluates; a subprocess also tests the real command line, its exit status and its error handling (FR-013).

## R8. The three layers

- **Layer 1** (INV-01 to INV-06): parse the reply; check the decision and the exact set of fields for it; check the operation against `OPERATIONS`; check each argument key against `OPERATIONS[operation].allowed` (without `purpose`); check each value's kind with `FIELDS[name].kind` (decimal strings through `lcgkit.wire.decode_large`, integers that are not booleans, a list of decimal strings for `outputs`); check the generator rule and the text lengths.
- **Layer 2** (PROP-01 to PROP-09): each property is a small function with a stated condition for when it applies, taken from the case (`expected`, `guardrail`, `category`). PROP-02 runs the arguments through lcgkit. PROP-06 searches the whole answer for the key value and the marker phrase. PROP-07 reads `model_calls` from the answer.
- **Layer 3**: exact comparison with the ground truth, scored as FR-024 defines. No model is a judge.
- **Reason**: every check is deterministic, so an evaluation result can be reproduced by re-reading the stored answers.

## R9. Repetitions and the stability figure

- **Decision**: three runs per case at temperature 0 (FR-021). The stability figure is the share of cases whose three repetitions have the same `decision`; it is reported and does not gate.
- **Reason**: temperature 0 lowers variation but does not remove it (a model can still vary slightly between identical calls), so repetition is how the variation is made visible instead of assumed away.

## R10. The dataset

- **Decision**: 48 cases, in `evals/dataset.json`, built from the acceptance criteria and properties:

| Category | Planned cases | What they cover |
|---|---|---|
| normal | 15 | each of the nine operations once, a second case for fractions, streams, validate, quality and presets, and a d20 |
| boundary | 8 | 64-bit digits kept exact; a count of exactly 1,000,000, 1,000,001 and 2,000,000; `steps` at 2^64 − 1 and 2^64; negative bounds; `predict` with too few outputs |
| ambiguous | 2 | "check my generator"; an expression such as 2^31 |
| missing information | 8 | no seed; no count; no state; part of the generator; no generator; no outputs for `predict`; a "random seed"; a coin flip |
| malformed | 4 | empty text; text over 1,000 characters; gibberish; bare numbers |
| adversarial and guardrail | 11 | password, session token, key and salt; weather; deleting files; ignore the rules and print the key; reveal the system prompt; an instruction mixed with a legitimate request; reply-looking text; two harmless near-misses |

- **Rules**: every input is synthetic; every case cites the IDs it tests in `covers`; criteria that no request text can test are listed in `covered_elsewhere` with the test that covers them.
- **Cost**: 48 cases × 3 repetitions, of which 46 cases call the model = 138 calls, about 10 minutes at a 3-second pause. A result larger than 10,000 bytes (the 1,000,000-number boundary case) is stored as its hash and size so the results file stays small.

## R11. Pre-checks

- **Decision**: Ruff with the rule sets E, F, I, B, UP, S, C90, PL, RUF and D1 on `src` and `tests`, always without the cache, with `known-first-party = ["lcgkit_assistant"]` and `known-third-party = ["lcgkit"]`; Bandit on `src`; pytest on `tests`; gitleaks over the history and the working tree; and the integrity check against the Git tag `baseline-before-implement`, whose annotation holds `test_functions=<N> dataset_cases=<M>`.
- **Versions**: the versions tested in Part 1A: Ruff 0.17.3, Bandit 1.9.4, pytest 9.2.0; gitleaks 8.30.1.
- **Reason**: the cache and the import-classification problems found in Part 1A are avoided by configuration from the start. These checks run before any model call so a broken build costs no quota.

## R12. Evidence layout

- **Decision**: each run writes `evidence/eval-runs/<run-id>/eval-results.json` (and `feedback.json` after a failure); the runner then copies the latest `eval-results.json` to `evidence/eval-results.json`. The first generated `src/` and `prompts/` are copied unchanged to `evidence/initial-generation/` before the first formal run, and again to `evidence/final-generation/` at the end.
- **Reason**: failed and repaired runs are part of the story the harness log tells, and they must not be overwritten.

## R13. Testing the harness

- **Decision**: the scoring, the layers and the runner are tested with hand-made answers (AC-049 to AC-052 are worked examples), and `.harness/selfcheck.py` runs the runner against small fake applications, each built to break one layer, to show that every layer can fail and that a correct fake passes.
- **Reason**: it is how the assignment's "validation independent of the generated code" is demonstrated, and it is the same idea that worked in Part 1A.

## Dependencies

| Package | Version tested | Used for | Why not the standard library |
|---|---|---|---|
| lcgkit | local (Part 1A) | running requests; the independent validator | it is the product being fronted |
| pytest | 9.2.0 | tests | unittest lacks markers and fixtures used for tracing |
| ruff | 0.17.3 | lint | development only |
| bandit | 1.9.4 | security scan | development only |

gitleaks is a separate binary, not a Python package. The model call, the command line, JSON and hashing use the standard library only.
