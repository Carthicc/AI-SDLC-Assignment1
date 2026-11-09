# Command-line contract

Program name: `lcgkit-assistant` (console script) or `python -m lcgkit_assistant.cli`. Standard library `argparse`.

## Usage

| Command | Does | Model call |
|---|---|---|
| `lcgkit-assistant "request text"` | Handles one request text and prints the answer (see `answer.schema.json`) as one line of JSON with sorted keys | yes, unless the text is empty or over-long |
| `lcgkit-assistant --info` | Prints `{"model", "settings": {"temperature", "response_format"}, "prompt_sha256"}` as JSON | no; works without `GEMINI_API_KEY` |

## Exit status (FR-013)

| Status | Meaning |
|---|---|
| 0 | an answer was produced: `call` (run or rejected by lcgkit), `clarify` or `refuse` |
| 2 | only an application error was produced: `request-too-long`, `missing-api-key`, `model-unavailable`, `reply-not-json`, `invalid-reply` |

In every case the answer is printed to standard output as JSON. Diagnostic messages, if any, go to standard error and never contain the key.

## Environment

`GEMINI_API_KEY` must be set. With `uv`, `uv run --env-file .env lcgkit-assistant "..."` reads it from the ignored file `.env`.

## Example

```text
$ uv run --env-file .env lcgkit-assistant "Give me 5 numbers from minstd with seed 42"
{"model_calls": 1, "reply": {"arguments": {"count": 5, "preset": "minstd", "seed": "42"}, "decision": "call", "operation": "sequence"}, "result": {"cryptographically_secure": false, "next_state": "807934826", "outputs": ["705894", "1126542223", "1579310009", "565444343", "807934826"], "outputs_consumed": 5, "warnings": []}}
```
