"""Results and feedback files (task T011)."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_RESULT_BYTES = 10_000


def summarise_answer(answer: dict[str, Any]) -> dict[str, Any]:
    """Replace a result larger than 10,000 bytes by its hash and size.

    Task: T011. Covers: AC-045.
    """
    summary = copy.deepcopy(answer)
    if "result" in summary:
        text = json.dumps(summary["result"], sort_keys=True)
        if len(text.encode()) > MAX_RESULT_BYTES:
            summary["result"] = {"sha256": hashlib.sha256(text.encode()).hexdigest(), "bytes": len(text.encode())}
    return summary


def build_report(
    run_id: str,
    info: dict[str, Any],
    case_results: list[dict[str, Any]],
    metrics: dict[str, float],
    threshold: dict[str, Any],
    verdict: dict[str, Any],
    duration_seconds: float,
) -> dict[str, Any]:
    """The evaluation report, in the shape of contracts/eval-results.schema.json.

    Task: T011. Covers: FR-025, AC-045, SC-008.
    """
    cases = []
    for case in case_results:
        repetitions = [{**rep, "answer": summarise_answer(rep["answer"])} for rep in case["repetitions"]]
        cases.append({**case, "repetitions": repetitions})
    return {
        "run_id": run_id,
        "model": info.get("model"),
        "settings": info.get("settings"),
        "prompt_sha256": info.get("prompt_sha256"),
        "duration_seconds": round(duration_seconds, 1),
        "cases": cases,
        "metrics": metrics,
        "threshold": {"overall_minimum": threshold["overall_minimum"], **verdict},
        "verdict": verdict["verdict"],
    }


def build_feedback(case_results: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    """For each case that did not score 1.0: the case, the answers and what failed.

    Task: T011. Covers: FR-027, AC-046.
    """
    by_id = {case["id"]: case for case in cases}
    failed = []
    for result in case_results:
        if result["score"] >= 1.0:
            continue
        failed.append(
            {
                "case": by_id[result["id"]],
                "score": result["score"],
                "repetitions": [
                    {
                        "answer": summarise_answer(rep["answer"]),
                        "layer1": rep["layer1"],
                        "layer2": rep["layer2"],
                        "layer3": rep["layer3"],
                    }
                    for rep in result["repetitions"]
                ],
            }
        )
    return {"failed_cases": failed}


def write_run(
    root: Path,
    run_id: str,
    report: dict[str, Any],
    feedback: dict[str, Any],
    key: str | None = None,
    latest: bool = True,
) -> Path:
    """Write the run folder and, for a full run, copy the report to evidence/eval-results.json.

    Refuses to write if the key appears in the text.

    Task: T011. Covers: FR-025, AC-045, AC-046, AC-054.
    """
    results_text = json.dumps(report, indent=2, sort_keys=True)
    feedback_text = json.dumps(feedback, indent=2, sort_keys=True)
    if key and (key in results_text or key in feedback_text):
        raise ValueError("refusing to write: the API key appears in the output")
    folder = root / "evidence" / "eval-runs" / run_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "eval-results.json").write_text(results_text)
    if feedback["failed_cases"]:
        (folder / "feedback.json").write_text(feedback_text)
    if latest:
        (root / "evidence" / "eval-results.json").write_text(results_text)
    return folder
