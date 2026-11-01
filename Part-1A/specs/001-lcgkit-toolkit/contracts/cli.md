# Command-line contract

Program name: `lcgkit`. Standard library `argparse`; one subcommand per capability. Results go to standard output, errors to standard error (FR-034).

## Subcommands

| Subcommand | Inputs | Same operation as |
|---|---|---|
| `presets` | none | `GET /v1/presets` |
| `sequence` | generator, `--seed`, `--count`, `--purpose` | `POST /v1/sequence` |
| `integers` | generator, `--seed`, `--lo`, `--hi`, `--count`, `--purpose` | `POST /v1/integers` |
| `fractions` | generator, `--seed`, `--count`, `--purpose` | `POST /v1/fractions` |
| `jump` | generator, `--state`, `--steps`, `--purpose` | `POST /v1/jump` |
| `streams` | generator, `--seed`, `--streams`, `--length`, `--purpose` | `POST /v1/streams` |
| `validate` | generator | `POST /v1/validate` |
| `quality` | generator, `--seed`, `--sample-size`, `--bins` | `POST /v1/quality` |
| `predict` | `--outputs`, optional `--m`, `--a`, `--c`, `--hidden-bits`, `--k` | `POST /v1/predict` |

A *generator* is either `--preset NAME` or all of `--a A --c C --m M`. Giving both is an error. Option names are the field names in the data model, with underscores written as hyphens. Integers are given as plain decimal text. `--outputs` takes comma-separated integers, or `-` to read one integer per line from standard input.

## Output

- Default: readable text with the same values.
- `--json`: the same body the HTTP service would return, with large integers as decimal strings (FR-033). Identical input gives byte-identical output on repeated runs (FR-005).

## Exit status (FR-034)

| Status | Meaning |
|---|---|
| 0 | success |
| 2 | invalid input (any error code except `insecure-purpose`), including bad usage |
| 3 | refused purpose (`insecure-purpose`) |
| 1 | unexpected failure (a defect) |

On failure nothing is printed to standard output; the message, with the error code and field, goes to standard error.

## Examples (the worked example from the specification)

```text
$ lcgkit sequence --a 5 --c 3 --m 16 --seed 7 --count 5 --json
{"outputs": ["6", "1", "8", "11", "10"], "outputs_consumed": 5, "next_state": "10", "warnings": [], "cryptographically_secure": false}

$ lcgkit sequence --preset minstd --seed 1 --count 3 --purpose token ; echo $?
error insecure-purpose: ...
3
```
