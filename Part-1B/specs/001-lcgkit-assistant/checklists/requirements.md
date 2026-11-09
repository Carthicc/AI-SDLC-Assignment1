# Specification Quality Checklist: lcgkit-assistant — a Natural-Language Front End for lcgkit

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Feature**: [spec.md](../spec.md)

## Content Quality

- [ ] No implementation details (languages, frameworks, APIs) — **not met by design**: the model service (Google Gemini), its settings and the command line are part of what is being specified and evaluated
- [x] Focused on user value and business needs
- [ ] Written for non-technical stakeholders — **not met by design**: the audience is developers and reviewers, and the subject (checking a language model) needs technical vocabulary; the Terminology section defines each term
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — the five open questions were answered and are recorded under Clarifications
- [x] Requirements are testable and unambiguous (26 requirements, each covered by at least one AC — checked by script)
- [x] Success criteria are measurable (SC-001 to SC-009 use counts, rates or exact values)
- [ ] Success criteria are technology-agnostic — **not met by design** for SC-006 and SC-009, which name the API key and the code checks because those are what is measured
- [x] All acceptance scenarios are defined (AC-001 to AC-060, 9 user stories; every AC cites the requirement it checks)
- [x] Edge cases are identified
- [x] Scope is clearly bounded (Out of scope listed under Assumptions)
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [ ] Feature meets measurable outcomes defined in Success Criteria — verifiable only after implementation and evaluation

## Where the non-determinism requirements are in the specification

| Needed | Where |
|---|---|
| Output schema contract | Output contract (layer 1), FR-001 to FR-003 |
| Structural invariants | INV-01 to INV-06 |
| Behavioural properties checkable without exact text | PROP-01 to PROP-09 |
| Safety and guardrail rules | FR-007 to FR-011 |
| Evaluation threshold, declared before any final evaluation | FR-025, SC-003 to SC-005, Clarifications |
| How the score is calculated | FR-023, FR-024, AC-049 to AC-052 |
| Handling of run-to-run variation | FR-021, AC-042, AC-043 |
| Traceability of evaluation cases to the specification | FR-020 (`covers`), FR-028, AC-048 |

## Notes

- Every request text and expected result in the acceptance criteria was written from the lcgkit field table and its limits; the example numbers in AC-006 and AC-008 are the published glibc values used in Part 1A.
- The model's behaviour was not tried against these criteria before the specification was written; one small exploratory call with a throwaway prompt showed that a careless prompt invents operations and answers a password request with a question about the seed, which is why FR-002, FR-004 and FR-007 are stated as separate requirements.
- The unchecked items are by design (audience, named technology) or can only be confirmed after implementation and evaluation.
