# lcgkit

A toolkit for linear congruential generators (LCGs), the recurrence `x -> (a*x + c) mod m`. It is a Python library, a command-line tool and a stateless HTTP service, and all three give the same answers.

It can generate repeatable sequences, use well-known generators by name, check whether parameters give a full period, jump ahead, draw fair integers and fractions, report on sequence quality, split a sequence into streams, and show how a sequence can be predicted from what has been seen.

## Install

Python 3.12 and [uv](https://docs.astral.sh/uv/) are needed. From this folder:

```text
uv sync
```

The harness also uses gitleaks to scan for secrets: `brew install gitleaks` on macOS, or see the gitleaks documentation for other platforms.

## Command line

Every capability is a subcommand: `presets`, `sequence`, `integers`, `fractions`, `jump`, `streams`, `validate`, `quality`, `predict`. A generator is either `--preset NAME` or all of `--a`, `--c`, `--m`. Add `--json` for JSON. Integers are written as plain decimal text, and in JSON every integer that can exceed 2^53 is a decimal string.

```text
$ uv run lcgkit sequence --a 5 --c 3 --m 16 --seed 7 --count 5 --json
{"cryptographically_secure": false, "next_state": "10", "outputs": ["6", "1", "8", "11", "10"], "outputs_consumed": 5, "warnings": []}

$ uv run lcgkit validate --a 1103515245 --c 24680 --m 2147483648 --json
$ uv run lcgkit jump --preset minstd --state 1 --steps 10000 --json
$ uv run lcgkit quality --preset minstd --seed 1 --sample-size 10000 --bins 10
```

Success exits with 0, invalid input with 2 and a refused purpose with 3. Errors go to standard error as `error <code>: <message>` and nothing is written to standard output. `uv run lcgkit <subcommand> --help` lists the options.

## HTTP service

```text
uv run lcgkit-serve            # listens on 127.0.0.1:8000, option --port
curl -s -X POST localhost:8000/v1/sequence \
  -H 'content-type: application/json' \
  -d '{"a":"5","c":"3","m":"16","seed":"7","count":5}'
```

The routes are `POST /v1/sequence`, `/v1/integers`, `/v1/fractions`, `/v1/jump`, `/v1/streams`, `/v1/validate`, `/v1/quality`, `/v1/predict` and `GET /v1/presets`. Invalid input gets status 400 and a refused purpose status 403, both with a structured error body. The OpenAPI description is served at `/openapi.json`. Nothing is stored between requests, and there is no authentication, so it is meant for local use.

## Harness

```text
uv run python .harness/run_harness.py
```

The runner executes eleven gates (lint, function length, types, security, secrets, dependency audit, tests with coverage, mutation testing, OpenAPI contract tests, integrity and traceability) and ends with a single `PASS` or `FAIL`. Each run writes `results.json`, the captured output of every gate and, after a failure, `feedback.json` to `evidence/harness-results/<run-id>/`. `uv run python .harness/selfcheck.py` shows that each gate can fail on a deliberately bad input. The integrity gate compares the protected files with the Git tag `baseline-before-implement`.

## Layout

`src/lcgkit/` holds the code: `core/` has the pure functions where the numbers are computed, and `ops.py`, `fields.py` and `wire.py` form the shared request path used by `cli.py` and `service.py`. `tests/` holds the tests written from the acceptance criteria, with an independent reference calculation in `tests/oracle/`. `.harness/` holds the gates. `specs/001-lcgkit-toolkit/` holds the specification, plan, tasks and the sources for every threshold and preset (`references.md`). `evidence/` holds the first and final generated code and the harness results.

## Security

An LCG is not cryptographically secure, and every successful answer says so with `cryptographically_secure: false`. Requests that declare a purpose such as a token, key, password or session are refused. The purpose guard relies on the declared purpose and cannot catch misuse that is not declared.

The quality checks are conventional, not proofs: a sound generator is flagged by chance in about 1% of samples per check, and passing does not show that a generator is random or secure.
