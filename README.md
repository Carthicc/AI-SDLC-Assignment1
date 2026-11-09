# AI-Augmented SDLC — Assignment 1: Spec-Driven Development and Harness Engineering

Submission for SEZG534 (AI-Augmented Software Development Life Cycle), BITS Pilani.

Two small applications are built with the GitHub Spec Kit workflow (constitution, specify, clarify, plan, tasks, analyze, implement). Each is checked by a harness that is independent of the generated code.

| Folder | Application | Kind |
|---|---|---|
| `Part-1A/` | **lcgkit**, a linear congruential generator toolkit (library, command line, HTTP service) | Deterministic |
| `Part-1B/` | An application that uses an AI model, with a three-layer evaluation harness | Non-deterministic |

## Use of AI assistance

This assignment was developed with some help from AI. I used Claude (through Claude Code) as a coding agent to draft the Spec Kit artifacts and to write implementation and harness code, under my direction and review. The harness logs and the reflection answers are written by me from the real evidence, as the assignment requires.

## Part 1A: lcgkit

A library, command line and HTTP service for linear congruential generators, with a specification, an independent test oracle and an eleven-gate harness. How to install, run and check it is in [`Part-1A/README.md`](Part-1A/README.md).

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
```
