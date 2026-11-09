# Fresh-request check

The evaluation dataset was also what guided the prompt repairs, so a score of 1.000 on it does not show how the assistant handles wording it has not been repaired against. This folder holds a separate check on 22 requests that are in neither the dataset nor the prompt.

- `run_fresh_check.py` holds the requests and their expected answers and runs each once through the real application, scoring it with the harness's three layers. It has no pass mark and nothing in `src/` or `prompts/` was changed because of its result.
- `results.json` is the run of the first 21 requests (F01 to F21): 20 scored 1.0.
- F09 scored 0, and the assistant's reply was the call that was expected. The request was badly made: its twelve outputs do not come from any generator, so lcgkit rejected them (`insufficient-data`, "no multiplier and increment fit these outputs") and layer 2 flagged the rejected call. F22 asks the same thing with outputs from a real generator, and `results-F22.json` shows it scored 1.0.

All 21 valid requests therefore scored 1.0: a plain request for each of the nine operations, three missing values, a generator with part of its numbers missing, an ambiguous request, a refusal for each of the three reasons, an instruction mixed with a real request, a harmless near-miss, a count above the limit, a negative range, and a greeting.

This is a small sample of one run each at temperature 0, so it is evidence of generalisation and not a measurement of it.
