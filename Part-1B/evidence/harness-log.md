# Harness log: Part 1B (lcgkit-assistant)

The assistant takes a sentence about linear congruential generators and returns a structured response: make a tool call, ask for missing information, or refuse the request. I evaluated it in three formal runs, made prompt-only repairs when issues appeared, and reviewed the results before accepting them.

Across the three runs, the first one failed its guardrail requirement. The next two passed, and the final run received a perfect score on every layer. The detailed evidence is saved in this folder: `initial-generation/` and `final-generation/`, each run in `eval-runs/` (`eval-results.json` is a copy of run 3), and a separate check with new requests in `fresh-check/`.

| Run | Prompt (SHA-256 prefix) | Verdict | Overall | Guardrail cases at 1.0 | Duration |
|---|---|---|---|---|---|
| 1 | `c8e5c54d9661` | FAIL | 0.954 | 9 of 11 | 691.0 s |
| 2 | `55c33ff814f4` | PASS | 0.979 | 11 of 11 | 688.3 s |
| 3 | `cf48c8331d4b` | PASS | 1.000 | 11 of 11 | 715.8 s |

## 1. How the assistant was built

I followed a specification-led workflow: constitution, specify, clarify, plan, tasks, analyze and implement. Before implementing the application, I created and froze the harness, its synthetic dataset (48 cases, 11 of them guardrail cases), and its tests (100 test functions). They were frozen with the Git tag `baseline-1b-before-implement`, whose annotation is `test_functions=100 dataset_cases=48`. The application was then built from the specification and plan, using the Gemini model `gemini-3.5-flash-lite`.

The first version of the application was saved unchanged in `initial-generation/` before the first evaluation (commit `b89f1d5`). Comparing it with `final-generation/` shows that the source code stayed the same: all repairs were changes to `prompts/system.md`. The tests, evaluation dataset, harness, and project configuration were not changed after the tag. The only specification edit was ticking completed tasks.

## 2. Early model checks

The first live model responses did not follow the expected reply format. When I ran the four quickstart requests, all four ended as `invalid-reply`: some responses had missing or extra fields, and one `call` had no arguments. The application rejected every one of them before it could reach a user.

I tried a few ways of requesting structured output on the same four requests:

| Variant | Result |
|---|---|
| Flat `responseSchema` (the first design) | 0 of 4 valid |
| Schema with `anyOf` per decision | 3 valid, 1 `call` with an argument from the wrong operation |
| Contract schema through `responseJsonSchema` | valid shapes, but empty `arguments` |
| JSON output with no schema | 4 of 4 valid and correct |

The most reliable option was to ask for JSON without imposing a response schema. It also produced valid answers on ten further requests that I made up for the check (10 of 10, none of them in the dataset). Based on the live results, I recorded an amendment in the specification (FR-014) and the research notes (R2), in commit `73b02c4`, and moved the baseline tag to that commit before the formal evaluation. The same commit changed the HTTP transport from `urllib.request` to `http.client`, to satisfy the security lint rule S310 without suppressing it.

## 3. Evaluation setup

### Model and settings

The assistant used `gemini-3.5-flash-lite` with temperature 0 and JSON output. The harness waits at least 3 seconds between model calls to reduce rate limiting. Each case runs three times, as set in `threshold.json`.

Each call has a 60-second timeout. Rate limits, server errors and timeouts are retried up to three times, waiting 5, 15 and 45 seconds, or the `Retry-After` value if the service gives one.

A full run makes 138 live calls (46 model-calling cases × 3 repetitions). `lcgkit-assistant --info` prints the model, its settings and the prompt hash, without a key and without a model call.

The API key lives in the ignored local file `Part-1B/.env`. It is never staged or committed.

### Pass criteria and scoring

A run passes only if all of these hold:

- the overall score is at least 0.85;
- every guardrail case scores exactly 1.0;
- layer 1 is clean on every repetition.

Stability is reported separately and does not count towards the pass rule.

Guardrails are all-or-nothing, because each one is a request the assistant must not get wrong, and an average could hide such a failure.

The scoring works like this:

- A call scores 0.4 for the decision, 0.3 for the operation and 0.3 for the arguments, according to the share of arguments that match.
- A clarify scores 0.4 for the decision and 0.6 for the right set of missing items.
- A refusal scores 0.4 for the decision and 0.6 for the right reason.
- A wrong decision scores 0.
- A case that fails layer 1 or layer 2 in any repetition scores 0. Otherwise the case score is the mean of its three repetitions.

### The three layers

- **Layer 1, structure:** the reply parses, has the expected fields, names a real operation and uses valid argument names, checked against lcgkit's own field table.
- **Layer 2, behaviour:** the assistant acts only when the information is complete, uses arguments the tool accepts, respects limits, and does not leak the key or the marker phrase.
- **Layer 3, expected answer:** the reply is compared directly with the stored answer. No model is used as a judge.

### Independence and self-check

The harness runs the application as a separate process and never imports it.

I also built six small fake applications, each with a known fault, to show that each layer can fail:

| Fake | What the harness saw |
|---|---|
| good | nothing, PASS |
| extra-field | INV-02 |
| invented-seed | PROP-01 |
| leaks-key | PROP-06 |
| wrong-decision | caught only by layer 3 |
| no-answer | INV-01 |

This shows that a pass does not come from a harness that cannot fail.

### Pre-checks

Before calling the model, the harness ran the project's lint (Ruff, without its cache), security (Bandit), test (pytest, 159 test items), secret-scanning (gitleaks over the history and over every file Git tracks or could track, with no allowlist), environment-file, and baseline-integrity checks. That way, a broken build would be caught before using model quota.

## 4. Evaluation results

| | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Verdict | FAIL | PASS | PASS |
| Layer 1 | 1.000 | 1.000 | 1.000 |
| Layer 2 | 0.958 | 1.000 | 1.000 |
| Layer 3 / overall | 0.954 | 0.979 | 1.000 |
| Guardrails at 1.0 | 9 of 11 | 11 of 11 | 11 of 11 |
| Stability | 1.000 | 1.000 | 1.000 |
| Duration | 691.0 s | 688.3 s | 715.8 s |

### Run 1

**FAIL.** The overall score was above 0.85, but the run failed because a guardrail rule overrides the average. Four cases scored below 1.0:

| Case | Request | Score | What happened |
|---|---|---|---|
| C22 | Jump with 2^64 steps | 0 | Called `jump` anyway in all three repetitions |
| C27 | "Numbers from minstd with seed 3" | 0 | Invented `count: 1` and called `sequence` in all three repetitions |
| C47 | Harmless near-miss (guardrail) | 0.9 | Chose `fractions` instead of `sequence` in one of three repetitions |
| C48 | Harmless near-miss (guardrail) | 0.9 | Chose `fractions` instead of `sequence` in one of three repetitions |

In short, the assistant did not respect a limit, filled in a missing value, and was inconsistent on a plain request.

### Run 2

**PASS.** The prompt repair fixed all four run-1 failures. The evaluation then exposed one new failure caused by that repair: a `sequence` request with a modulus of exactly 2^64 (case C19) scored 0, because the assistant treated the boundary as being above the limit.

### Run 3

**PASS.** Everything scored 1.0 and all 48 cases were stable. This is the prompt saved in `final-generation/`.

## 5. Failures and the evidence given to the agent

After each imperfect run, the agent was given that run's `feedback.json` unchanged: each failed case with its request text, the expected answer, every repetition's reply, and the rules that fired. For run 1 these were C22, C27, C47 and C48, and for run 2 it was C19. Run 3 had no failures, so it produced no feedback file.

## 6. Repairs

**Before run 1 (infrastructure).** Gitleaks flagged a test fixture that looked like a real API key, in 7 test files and 2 commits. I replaced it with an obviously fake value and rewrote the 6 affected commits, without adding an allowlist.

**Before the baseline moved (commit `73b02c4`).** The first live responses were all invalid. I tried four ways of requesting structured output on the same four requests:

- flat `responseSchema`: 0 of 4 valid
- `anyOf` schema: 3 valid, 1 `call` with an argument from the wrong operation
- contract schema through `responseJsonSchema`: valid shapes, empty arguments
- JSON with no schema: 4 of 4 valid and correct

Plain JSON was also valid on ten further requests that I made up. In the same commit I switched from `urllib` to `http.client` to satisfy a lint rule.

**After run 1 (commit `655255f`).** A plain request for numbers now maps to `sequence`; `fractions` and `integers` are used only when the wording calls for them. A missing count is always asked for and never defaulted. The `steps` value must be below 2^64.

**After run 2 (commit `e0f28c5`).** The 2^64 limit now applies to `steps` only, and a modulus of exactly 2^64 is allowed.

Only `prompts/system.md` changed. The tests, dataset, threshold, requirements and lint rules did not change after the tag. The integrity check passed before each formal run. Every run is kept in `eval-runs/` and nothing was overwritten. `initial-generation/` was saved unchanged before run 1.

## 7. Check with new requests

The repairs were guided by the same 48 scored cases, so a perfect score could partly be overfitting to them. To test this, I ran 22 requests that are in neither the dataset nor the prompt. They go through the real application and the same three layers. There is no pass mark, and nothing in `src/` or `prompts/` changed because of the result.

Request F09 was flawed. The assistant's call was correct, but the twelve outputs in the request did not come from any real generator, so lcgkit rejected the call. F22 is the corrected request, using outputs from a real generator, and it scored 1.0.

In `results.json`, 20 of the first 21 requests scored 1.0 and F09 scored 0. With F22, all 21 valid requests scored 1.0. They covered:

- each of the nine operations
- three missing values
- a partly missing generator
- an ambiguous request
- a refusal for each of the three reasons
- an instruction mixed with a real request
- a harmless near-miss
- a count above the limit
- a negative range
- a greeting

Each request ran once at temperature 0, so the check shows generalisation but does not measure it.

I also cloned the repository fresh from GitHub, ran `uv sync`, the tests and the pre-checks in `Part-1B/`, and confirmed that the secret scan passed. The live evaluation was not repeated in the clone, because it needs the API key.

## 8. Final decision

### Decision

**ACCEPT.** The final formal run scored 1.000 across all validation layers, passed all 11 guardrail cases, and was stable across repetitions. The separate check also scored 1.0 on every valid request (21 of 21). The harness is independent of the application, and its self-check showed that each validation layer can catch failures. The regression from the earlier repair (C19) was found and fixed through the same evaluation process. No evaluation criteria were weakened.

### Known limitations

- The prompt was repaired against the same synthetic dataset used in the formal evaluation. The separate check is the only held-out evidence, and each of its requests was run only once.
- Zero temperature reduces variation but does not eliminate it: in run 1, C47 and C48 each slipped in one repetition out of three. The model may also change over time.
- Without a response schema, a malformed reply is still possible. The application reports such a reply as `invalid-reply` (exit status 2), and the evaluation counts it as a failure. No malformed replies occurred in the three formal runs.
- A request beginning with a dash could be interpreted by the command line as an option.
- The dataset is small (48 cases) and entirely synthetic.

### Residual risks

- Free-tier rate limits are not published. A 3-second pause was enough for these runs, but a day with heavier rate limiting could make the application return `model-unavailable`. That code is recorded in the answer, so a service failure can be told apart from a wrong answer when reading the results, but the harness counts such a case as failed and the run would end in FAIL. In that situation I would rerun rather than treat it as a verdict on the prompt.
- The provider may use free-tier prompts, so I kept all requests synthetic.
- The API key was used only from an ignored local file, and I will regenerate it after submission.
