"""Loads the evaluation dataset and checks it against the specification (task T012)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

OPERATIONS = ("presets", "sequence", "integers", "fractions", "jump", "streams", "validate", "quality", "predict")
CATEGORIES = ("normal", "boundary", "ambiguous", "missing-information", "malformed", "adversarial")
MIN_CASES = 30
MIN_CALL_CASES = 2
MIN_GUARDRAIL = 6
MIN_NEAR_MISS = 2
ID_PATTERN = re.compile(r"^(AC-\d{3}|INV-\d{2}|PROP-\d{2})$")
REQUIRED = ("id", "category", "text", "expected", "guardrail", "covers")


def load(path: Path) -> dict[str, Any]:
    """Read the dataset file."""
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("the dataset must be a JSON object")
    return data


def spec_ids(spec_path: Path) -> set[str]:
    """The AC, INV and PROP IDs defined in the specification."""
    text = spec_path.read_text()
    found = set(re.findall(r"^\| (AC-\d{3}) \|", text, re.M))
    found |= set(re.findall(r"^- \*\*((?:INV|PROP)-\d{2})\*\*", text, re.M))
    return found


def _case_problems(case: dict[str, Any]) -> list[str]:
    cid = case.get("id", "?")
    problems = [f"{cid}: missing field {name}" for name in REQUIRED if name not in case]
    expected = case.get("expected")
    if isinstance(expected, dict) and "decision" not in expected and "error" not in expected:
        problems.append(f"{cid}: expected needs a decision or an error")
    if case.get("category") not in CATEGORIES:
        problems.append(f"{cid}: unknown category {case.get('category')!r}")
    return problems


def _shape_problems(cases: list[dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    if len(cases) < MIN_CASES:
        problems.append(f"only {len(cases)} cases, at least {MIN_CASES} are needed")
    ids = [case.get("id") for case in cases]
    problems += [f"duplicate case id {cid}" for cid in sorted({i for i in ids if ids.count(i) > 1})]
    for case in cases:
        problems += _case_problems(case)
    return problems


def _minimum_problems(cases: list[dict[str, Any]]) -> list[str]:
    problems = []
    for operation in OPERATIONS:
        count = sum(
            1 for case in cases
            if case.get("expected", {}).get("decision") == "call" and case["expected"].get("operation") == operation
        )
        if count < MIN_CALL_CASES:
            problems.append(f"operation {operation} has {count} call cases, at least {MIN_CALL_CASES} are needed")
    present = {case.get("category") for case in cases}
    problems += [f"no case in category {name}" for name in CATEGORIES if name not in present]
    guardrails = [case for case in cases if case.get("guardrail")]
    near = [c for c in guardrails if c["expected"].get("decision") != "refuse" and "PROP-05" in c.get("covers", [])]
    if len(guardrails) < MIN_GUARDRAIL:
        problems.append(f"only {len(guardrails)} guardrail cases, at least {MIN_GUARDRAIL} are needed")
    if len(near) < MIN_NEAR_MISS:
        problems.append(f"only {len(near)} near-miss cases, at least {MIN_NEAR_MISS} are needed")
    return problems


def _traceability_problems(dataset: dict[str, Any], spec: set[str]) -> list[str]:
    cases = dataset.get("cases", [])
    elsewhere = set(dataset.get("covered_elsewhere", {}))
    covered = {i for case in cases for i in case.get("covers", [])}
    problems = [f"unknown id {i} in covers" for i in sorted(covered - spec)]
    problems += [f"unknown id {i} in covered_elsewhere" for i in sorted(elsewhere - spec)]
    problems += [f"{i} is covered by a case and listed in covered_elsewhere" for i in sorted(covered & elsewhere)]
    problems += [f"{i} has no case and is not in covered_elsewhere" for i in sorted(spec - covered - elsewhere)]
    problems += [f"covers entry {i} is not an ID" for i in sorted(covered) if not ID_PATTERN.match(i)]
    return problems


def validate(dataset: dict[str, Any], spec_path: Path) -> list[str]:
    """Return the problems of a dataset (empty means it is valid).

    Task: T012. Covers: FR-020, FR-028, AC-048, SC-001, SC-002.
    """
    cases = dataset.get("cases")
    if not isinstance(cases, list):
        return ["the dataset has no list of cases"]
    problems = _shape_problems(cases)
    if problems:
        return problems
    return _minimum_problems(cases) + _traceability_problems(dataset, spec_ids(spec_path))
