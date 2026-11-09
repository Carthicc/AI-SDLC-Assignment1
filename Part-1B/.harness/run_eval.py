"""The single evaluation runner (task T015).

Usage: uv run --env-file .env python .harness/run_eval.py [--run-id ID] [--min-interval SECONDS]
       [--app "command"] [--only C01,C02]
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import app
import dataset
import prechecks
import report
import scoring

ROOT = Path(__file__).resolve().parents[1]
SPEC = Path("specs/001-lcgkit-assistant/spec.md")


def load_threshold(root: Path) -> dict[str, Any]:
    """Read the declared threshold."""
    return json.loads((root / ".harness" / "threshold.json").read_text())


def run_cases(
    cases: list[dict[str, Any]],
    command: list[str],
    threshold: dict[str, Any],
    sleep: Callable[[float], None] = time.sleep,
    min_interval: float | None = None,
    env: dict[str, str] | None = None,
    log: Callable[[str], None] = print,
) -> list[list[dict[str, Any]]]:
    """Run every case the declared number of times; pause after each run that called the model."""
    pause = threshold["min_interval_seconds"] if min_interval is None else min_interval
    all_answers = []
    for case in cases:
        answers = []
        for _ in range(threshold["repetitions"]):
            answer = app.run_app(case["text"], command, threshold["call_timeout_seconds"], env)
            answers.append(answer)
            if answer.get("model_calls", 0) > 0:
                sleep(pause)
        log(f"{case['id']}: {len(answers)} runs")
        all_answers.append(answers)
    return all_answers


def evaluate(
    cases: list[dict[str, Any]], answers: list[list[dict[str, Any]]], threshold: dict[str, Any], key: str | None
) -> tuple[list[dict[str, Any]], dict[str, float], dict[str, Any]]:
    """Score all cases and compute the metrics and the verdict."""
    secrets = {"key": key, "marker": threshold["marker_phrase"]}
    results = [
        scoring.evaluate_case(case, runs, secrets, threshold["weights"]) for case, runs in zip(cases, answers, strict=True)
    ]
    metrics = scoring.compute_metrics(results)
    return results, metrics, scoring.verdict(results, metrics, threshold)


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate lcgkit-assistant against the dataset.")
    parser.add_argument("--run-id", default=time.strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--min-interval", type=float, default=None)
    parser.add_argument("--app", default=None, help="command that starts the application")
    parser.add_argument("--only", default=None, help="comma-separated case IDs (a partial run)")
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser.parse_args(argv)


def _print_report(metrics: dict[str, float], result: dict[str, Any], seconds: float, label: str) -> None:
    for name, value in metrics.items():
        print(f"{name:<22}{value:.3f}")
    print(f"{'duration_seconds':<22}{seconds:.1f}")
    print(f"overall >= {result['overall_minimum']}: {result['overall_held']}; guardrails: {result['guardrails_held']}; layer 1: {result['layer1_held']}")
    print(label)


def main(
    argv: list[str] | None = None,
    prechecks_fn: Callable[[Path], list[dict[str, Any]]] = prechecks.run_prechecks,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Run the pre-checks, the dataset check and the evaluation; return 0 only on PASS.

    Task: T015. Covers: FR-021, FR-022, FR-025, FR-026, FR-027, FR-030, AC-044, AC-047, AC-052, SC-008.
    """
    args = _parse(argv)
    root, threshold = args.root, load_threshold(args.root)
    checks = prechecks_fn(root)
    for check in checks:
        print(f"{check['status']}  {check['name']}")
    if any(check["status"] != "PASS" for check in checks):
        print("FAIL")
        return 1
    data = dataset.load(root / "evals" / "dataset.json")
    problems = dataset.validate(data, root / SPEC)
    if problems:
        print("\n".join(problems), "\nFAIL", sep="\n")
        return 1
    cases = [c for c in data["cases"] if args.only is None or c["id"] in args.only.split(",")]
    command = shlex.split(args.app) if args.app else app.default_command()
    started = time.perf_counter()
    info = app.app_info(command)
    answers = run_cases(cases, command, threshold, sleep, args.min_interval)
    key = os.environ.get("GEMINI_API_KEY")
    results, metrics, result = evaluate(cases, answers, threshold, key)
    seconds = time.perf_counter() - started
    full = args.only is None
    built = report.build_report(args.run_id, info, results, metrics, threshold, result, seconds)
    report.write_run(root, args.run_id, built, report.build_feedback(results, cases), key, latest=full)
    label = result["verdict"] if full else "PARTIAL"
    _print_report(metrics, result, seconds, label)
    return 0 if full and result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
