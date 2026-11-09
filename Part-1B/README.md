# lcgkit-assistant

A natural-language front end for [lcgkit](../Part-1A/README.md), the linear congruential generator toolkit. You type a request in plain English; Google Gemini decides whether the request is clear enough to run, needs a question first, or must be refused; and when it is clear, lcgkit does all the calculation. The model never calculates anything.

```text
$ uv run --env-file .env lcgkit-assistant "Give me 5 numbers from minstd with seed 42"
{"model_calls": 1, "reply": {"arguments": {"count": 5, "preset": "minstd", "seed": "42"}, "decision": "call", "operation": "sequence"}, "result": {"cryptographically_secure": false, "next_state": "807934826", "outputs": ["705894", "1126542223", "1579310009", "565444343", "807934826"], "outputs_consumed": 5, "warnings": []}}
```

Because a model's answers vary from run to run, the assistant is judged by an evaluation harness that checks structure, behaviour and correctness on a dataset of 48 requests, each run three times, and not by comparing exact wording.

## Install

Python 3.12 and [uv](https://docs.astral.sh/uv/) are needed. From this folder:

```text
uv sync
brew install gitleaks      # used by the evaluation's secret scan; other platforms: see the gitleaks documentation
```

lcgkit is installed from `../Part-1A` as a local dependency.

## The API key

The assistant reads the key from the environment variable `GEMINI_API_KEY`. Create a free key in Google AI Studio and put it in a file named `.env` in this folder:

```text
GEMINI_API_KEY=<your key>
```

`.env` is ignored by Git and must never be committed; `.env.example` shows the format. The free tier may use prompts to improve Google's products, so use only made-up request texts. The key is never printed, logged or written to any result file.

## Run it

```text
uv run --env-file .env lcgkit-assistant "your request"
uv run lcgkit-assistant --info
```

The answer is one line of JSON with `reply` (what the model decided), `result` (lcgkit's answer, for a `call`) or `error`, and `model_calls`. A reply is one of three decisions: `call` (run an lcgkit operation), `clarify` (a question, with the values that are missing) or `refuse` (with a reason: `insecure-purpose`, `out-of-scope` or `unsafe-instruction`). The assistant never invents a missing value and refuses requests whose purpose is a token, key, password or similar, because LCG output is predictable. Text typed by the person is treated as data, never as instructions.

The exit status is 0 when an answer was produced (including a question, a refusal and an lcgkit rejection) and 2 for an application error: `request-too-long`, `missing-api-key`, `model-unavailable`, `reply-not-json` or `invalid-reply`. `--info` prints the model, its settings and the SHA-256 of the system prompt, without a model call or a key.

## Tests

```text
uv run pytest tests -q
```

These test the deterministic parts (the rules, the contract check, the model client and the command line) with a fake model service, and the evaluation harness itself, without the network.

## Evaluation

```text
uv run --env-file .env python .harness/run_eval.py
uv run python .harness/selfcheck.py
```

The runner first checks the application code (lint, security scan, tests, secret scan and the protected files against the Git tag `baseline-1b-before-implement`), then runs every case in `evals/dataset.json` three times through the command line, checks each answer in three layers (structure, properties, comparison with the expected answer), and prints the six metrics and one `PASS` or `FAIL`. A run passes only if the overall score is at least 0.85, every guardrail case scores 1.0 and layer 1 passes in every repetition. The whole run takes about ten minutes. `selfcheck.py` shows that each layer can fail, using fake applications built to break one layer each.

Results are written to `evidence/eval-runs/<run-id>/` (`eval-results.json`, and `feedback.json` after a failure); `evidence/eval-results.json` is a copy of the latest full run.

## Layout

`src/lcgkit_assistant/` holds the application: `config.py` (named limits and settings), `contract.py` (the check of a reply), `model.py` (the Gemini call with its retries), `assistant.py` (the flow for one request) and `cli.py` (the command line). `prompts/system.md` is the system prompt. `tests/` holds the unit tests and the tests of the harness. `evals/dataset.json` holds the evaluation cases. `.harness/` holds the runner, the three layers, the scoring and the fake applications. `specs/001-lcgkit-assistant/` holds the specification, plan, tasks and contracts. `evidence/` holds the first and final generated code and the evaluation runs.
