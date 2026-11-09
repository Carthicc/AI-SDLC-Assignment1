# Harness log: Part 1A (lcgkit)

## 1. First generation and its context

The Spec Kit stages were completed and committed, and gave 48 requirements, 90 acceptance criteria and 90 tasks. The 11 gates, the oracle and the tests were written and frozen with a baseline tag before the agent was given any implementation work. The agent then implemented the tasks, using only the approved artifacts, and the first-generation snapshot was copied into the evidence folder before the harness was run.

## 2. Harness runs and outcomes

### Run 1

Nine of the 11 gates passed. The tests gate failed because branch coverage was 93.69% (the required minimum is 95%), although all 486 tests passed. The mutation gate also failed.

### Run 2

The tests gate passed, but the mutation gate failed again.

### Run 3

All 11 gates passed, and mutation testing killed 87% of the 1,130 mutants (983 of 1,130).

### Run 4 (and the fresh-clone check)

A fresh-clone check made after run 3 showed the lint gate failing with 30 import-order findings. After the repair, all 11 gates passed in run 4, and they also passed in a fresh clone from the repository.

## 3. Failures and the evidence given to the agent

Branch coverage was recorded at 93.69% in run 1. The mutation gate reported errors in runs 1 and 2. The 30 lint findings were found only in the fresh-clone check, because Ruff's cache had hidden them in runs 1 to 3. The agent was given `feedback.json` for the failed gates.

## 4. Repairs and re-validation

The first repair made coverage measure subprocesses and copied the package files for mutation testing, but the mutation gate still failed. The second repair copied the README and the contracts folder and excluded the contract tests from mutation runs, after which all gates passed in run 3. The third repair reordered the test imports and made the lint gate run without its cache, after which all gates passed in run 4 and in a fresh clone. Every repair was recorded as an amendment with a new baseline tag. The source code was not changed after the first generation, and no threshold, test or requirement was weakened.

## 5. Final human decision

**ACCEPT.** In run 4 the code passed all 11 gates, with an 87% mutation score and 96.72% coverage, and it passed again in a fresh clone.

Known limitations: of the 124 surviving mutants, most are in the predictor and number-theory code; the 23 timeouts are counted against the mutation score; the contract tests are excluded from mutation runs; and there are two gaps in the specification (the low-bit periods for small power-of-two moduli, and the independence check on a constant sequence).

Reason for accepting: every automated gate passes on a clean checkout, the limitations are known, bounded and documented, and no gate was weakened to get here. All three amendments are also recorded.
