# Quickstart: checking that lcgkit works end to end

These scenarios describe the finished toolkit. They are the checks to run once implementation is complete; each cites the acceptance criterion it proves. Expected values come from the specification, which in turn were calculated independently.

## Setup

```text
uv sync                    # installs the pinned dependencies (Python 3.12)
```

## 1. Command line

| Check | Command | Expected | Criterion |
|---|---|---|---|
| Worked example | `lcgkit sequence --a 5 --c 3 --m 16 --seed 7 --count 5 --json` | `outputs` = `["6","1","8","11","10"]`, `next_state` = `"10"` | AC-001 |
| Preset | `lcgkit sequence --preset glibc-type0 --seed 1 --count 3 --json` | `["1103527590","377401575","662824084"]` | AC-015 |
| Parameter check | `lcgkit validate --a 1103515245 --c 24680 --m 2147483648 --json` | `not-full-period`, one reason: `increment-not-coprime` | AC-023 |
| Jump ahead | `lcgkit jump --preset minstd --state 1 --steps 10000 --json` | `state` = `"1043618065"` | AC-030 |
| Fair integers | `lcgkit integers --a 5 --c 3 --m 16 --seed 7 --lo 1 --hi 3 --count 15 --json` | 1, 2 and 3 five times each | AC-035 |
| Quality | `lcgkit quality --preset minstd --seed 1 --sample-size 10000 --bins 10 --json` | chi-square 6.69, p-value 0.6694, verdict `no-defect-detected` | AC-057 |
| Predictor | `lcgkit predict --m 2147483648 --outputs 1103527590,377401575,662824084,1147902781,2035015474 --json` | recovers `a = 1103515245`, `c = 12345`; ten predictions | AC-074 |
| Refusal | `lcgkit sequence --preset minstd --seed 1 --count 3 --purpose token` | nothing on standard output, `insecure-purpose` on standard error, exit status 3 | AC-044 |

## 2. HTTP service

```text
uv run lcgkit-serve        # listens on 127.0.0.1:8000
curl -s -X POST localhost:8000/v1/sequence \
  -H 'content-type: application/json' \
  -d '{"a":"5","c":"3","m":"16","seed":"7","count":5}'
```

Expected body: the same JSON as the command-line worked example. `curl` with `"purpose": "token"` returns status 403 and an `insecure-purpose` error. The published description is at `/openapi.json` and matches `contracts/openapi.yaml`.

## 3. Harness

```text
uv run python .harness/run_harness.py
```

Expected: every gate prints its result, the runner ends with a single `PASS` or `FAIL`, exits 0 only on `PASS`, and writes `evidence/harness-results/<run-id>/results.json` together with the captured output of each gate. On a failure it also writes `feedback.json` for each failed gate: the failing rule or test, the expected behaviour and the observed one, the relevant requirement and criterion IDs.

## 4. Spot-check against the independent oracle

```text
uv run pytest tests/oracle -q
```

Expected: the oracle's own tests pass without importing anything from `src/`.
