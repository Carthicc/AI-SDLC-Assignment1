"""Shows that every layer of the harness can fail (task T017).

Runs the evaluation logic against small stand-in applications (fakes/fake_app.py), each built to
break one layer, and checks that the right layer notices. Exits 0 only if every mode behaved as
expected. Usage: uv run python .harness/selfcheck.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_eval

from fakes import fake_app

FAKE_KEY = "FAKE-KEY-0123456789"
COMMAND = [sys.executable, str(HERE / "fakes" / "fake_app.py")]
CASES = [
    {"id": "S1", "category": "normal", "text": fake_app.CALL_TEXT, "guardrail": False, "covers": [],
     "expected": {"decision": "call", "operation": "sequence", "arguments": fake_app.CALL_ARGUMENTS}},
    {"id": "S2", "category": "missing-information", "text": fake_app.CLARIFY_TEXT, "guardrail": False,
     "covers": [], "expected": {"decision": "clarify", "missing": ["seed"]}},
    {"id": "S3", "category": "adversarial", "text": fake_app.REFUSE_TEXT, "guardrail": True, "covers": [],
     "expected": {"decision": "refuse", "reason": "insecure-purpose"}},
    {"id": "S4", "category": "malformed", "text": "", "guardrail": False, "covers": [],
     "expected": {"decision": "clarify", "model_calls": 0}},
]


def _rules(results: list[dict[str, Any]], case_id: str, layer: str) -> set[str]:
    case = next(result for result in results if result["id"] == case_id)
    return {v["rule"] for rep in case["repetitions"] for v in rep[layer]}


def _run(mode: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    env = {**os.environ, "FAKE_MODE": mode, "GEMINI_API_KEY": FAKE_KEY}
    threshold = run_eval.load_threshold(HERE.parent)
    answers = run_eval.run_cases(CASES, COMMAND, threshold, sleep=lambda _s: None, env=env, log=lambda _m: None)
    results, _metrics, verdict = run_eval.evaluate(CASES, answers, threshold, FAKE_KEY)
    return results, verdict


def main() -> int:
    """Run every mode and print a table; return 0 only if each mode behaved as expected."""
    expectations = {
        "good": lambda r, v: v["verdict"] == "PASS",
        "extra-field": lambda r, v: "INV-02" in _rules(r, "S1", "layer1"),
        "invented-seed": lambda r, v: "PROP-01" in _rules(r, "S2", "layer2"),
        "leaks-key": lambda r, v: "PROP-06" in _rules(r, "S3", "layer2"),
        "wrong-decision": lambda r, v: v["verdict"] == "FAIL" and r[0]["score"] == 0,
        "no-answer": lambda r, v: v["verdict"] == "FAIL" and "INV-01" in _rules(r, "S1", "layer1"),
    }
    ok = True
    print(f"{'mode':<16}{'what the harness saw':<44}as expected")
    for mode, expect in expectations.items():
        results, verdict = _run(mode)
        seen = sorted(_rules(results, "S1", "layer1") | _rules(results, "S2", "layer2") | _rules(results, "S3", "layer2"))
        good = bool(expect(results, verdict))
        ok &= good
        print(f"{mode:<16}{(', '.join(seen) or 'nothing') + ' / ' + verdict['verdict']:<44}{'yes' if good else 'NO'}")
    print("SELFCHECK PASS" if ok else "SELFCHECK FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
