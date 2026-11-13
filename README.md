# AI-Augmented SDLC — Assignment 1: Spec-Driven Development and Harness Engineering

Submission for SEZG534 (AI-Augmented Software Development Life Cycle), BITS Pilani.

Two small applications are built with the GitHub Spec Kit workflow (constitution, specify, clarify, plan, tasks, analyze, implement). Each is checked by a harness that is independent of the generated code.

| Folder | Application | Kind |
|---|---|---|
| `Part-1A/` | **lcgkit**, a linear congruential generator toolkit (library, command line, HTTP service) | Deterministic |
| `Part-1B/` | **lcgkit-assistant**, a natural-language front end for lcgkit that uses Google Gemini, with a three-layer evaluation harness | Non-deterministic |

## Setup environment

| Item | Version or choice |
|---|---|
| Operating system | macOS 26.6.2 (Darwin 25.6.0), shell zsh |
| GitHub Spec Kit | `specify` 1.2.6.dev0, initialised in each part with the Claude Code integration (commands installed as skills) and the `sh` scripts; the choices are recorded in each part's `.specify/init-options.json` |
| Coding agent | Claude Code, in VS Code |
| Python and packages | Python 3.12 (`requires-python >=3.12,<3.13`), managed with uv 0.12.24 |
| Tools used by the harnesses | Ruff 0.17.3, Bandit 1.9.4, pytest 9.2.0, gitleaks 8.30.1 |
| Git | 2.54.0 |

## Use of AI assistance

This assignment was developed with some help from AI. I used Claude (through Claude Code) as a coding agent to draft the Spec Kit artifacts and to write implementation and harness code, under my direction and review. The harness logs and the reflection answers are written by me from the real evidence, as the assignment requires.

## Part 1A: lcgkit

A library, command line and HTTP service for linear congruential generators, with a specification, an independent test oracle and an eleven-gate harness. How to install, run and check it is in [`Part-1A/README.md`](Part-1A/README.md).

## Part 1B: lcgkit-assistant

A command-line assistant that turns a plain-English request into an lcgkit operation, asks when a value is missing and refuses insecure or unrelated requests. The model's answers vary, so it is judged by a three-layer evaluation harness (structure, properties, comparison with the expected answer) on a dataset of 48 requests, each run three times. How to install, run and evaluate it is in [`Part-1B/README.md`](Part-1B/README.md).

## Layout

```
Part-1A/
  .specify/        Spec Kit templates, scripts and the project constitution
  .claude/         Spec Kit commands installed as Claude Code skills
  specs/001-lcgkit-toolkit/    specification, plan, tasks, references, checklists
  src/ tests/      the code and the tests derived from the acceptance criteria
  .harness/        the quality gates and the runner
  evidence/        generated code snapshots and harness results
Part-1B/
  .specify/ .claude/           Spec Kit templates, scripts and skills, and the Part 1B constitution
  specs/001-lcgkit-assistant/  specification, plan, tasks, contracts
  src/ prompts/ tests/         the application, its system prompt and the tests
  evals/                       the evaluation dataset
  .harness/                    the evaluation runner, the three layers and the self-check
  evidence/                    generated code snapshots and evaluation runs
```
