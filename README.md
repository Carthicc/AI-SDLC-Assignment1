# AI-Augmented SDLC — Assignment 1: Spec-Driven Development and Harness Engineering

Submission for SEZG534 (AI-Augmented Software Development Life Cycle), BITS Pilani.

Two small applications are built with the GitHub Spec Kit workflow (constitution, specify, clarify, plan, tasks, analyze, implement). Each is checked by a harness that is independent of the generated code.

| Folder | Application | Kind |
|---|---|---|
| `Part-1A/` | **lcgkit**, a linear congruential generator toolkit (library, command line, HTTP service) | Deterministic |
| `Part-1B/` | An application that uses an AI model, with a three-layer evaluation harness | Non-deterministic |

## Use of AI assistance

This assignment was developed with some help from AI. I used Claude (through Claude Code) as a coding agent to draft the Spec Kit artifacts and to write implementation and harness code, under my direction and review. The harness logs and the reflection answers are written by me from the real evidence, as the assignment requires.

## Layout

```
Part-1A/
  .specify/        Spec Kit templates, scripts and the project constitution
  .claude/         Spec Kit commands installed as Claude Code skills
  specs/001-lcgkit-toolkit/    specification, references, checklists
Part-1B/
```
