# Specification Quality Checklist: lcgkit — Linear Congruential Generator Toolkit

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — no language, framework or library is named; "JSON" and "HTTP" appear only as the data format and interface type
- [x] Focused on user value and business needs
- [ ] Written for non-technical stakeholders — **not met by design**: the audience is developers and students, and the subject (modular arithmetic) needs technical vocabulary. Terminology section mitigates this.
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — the 3 raised in the first draft were resolved: maximum values per request = 1,000,000 (FR-004); quality report includes a verdict with fixed thresholds (FR-035 to FR-037); predictor covers known modulus, unknown modulus and truncated outputs with known parameters (FR-048 to FR-053).
- [x] Requirements are testable and unambiguous (56 requirements, each covered by at least one AC — checked by script)
- [x] Success criteria are measurable (SC-001 to SC-009 use counts, percentages or exact values)
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined (AC-001 to AC-089, 11 user stories; every AC cites the requirements it covers)
- [x] Edge cases are identified
- [x] Scope is clearly bounded (Out of scope listed under Assumptions)
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [ ] Feature meets measurable outcomes defined in Success Criteria — verifiable only after implementation
- [x] No implementation details leak into specification

## Notes

- Reference values used in the acceptance criteria (presets, small worked examples, jump-ahead identities, bounded-integer counts, quality statistics and verdicts, predictor recoveries) were computed with independent throwaway scripts kept outside the repository, before being written into the specification. MINSTD's and MINSTD-new's 10,000th outputs match the published Park–Miller check values; the chi-square p-value method matches the NIST/SEMATECH 1% critical values at 1, 2, 3, 10 and 100 degrees of freedom.
- The validator rule was cross-checked against brute force on all 89,439 triples with 2 <= m <= 64 (0 disagreements); this is the basis of SC-002.
- Threshold justification: sources, verbatim quotes and the list of decisions without a source are in `references.md`. NIST SP 800-22 Rev. 1a was read from the original PDF; the NIST/SEMATECH e-Handbook pages were fetched directly. Knuth's TAOCP Vol. 2 was not consulted.
- Known limitation recorded in the spec: RANDU and the glibc multiplier with an even increment pass the uniformity and serial-correlation checks at 10,000 samples.
- The remaining unchecked items are by design (audience) or can only be confirmed after implementation.
