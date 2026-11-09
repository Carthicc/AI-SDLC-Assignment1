"""Scores, metrics and the verdict (task T009). Imports nothing from the application."""

from __future__ import annotations

from statistics import mean
from typing import Any

from layers import properties, semantic, structure

TOLERANCE = 1e-9


def evaluate_repetition(
    case: dict[str, Any], answer: dict[str, Any], secrets: dict[str, Any], weights: dict[str, Any]
) -> dict[str, Any]:
    """Apply the three layers to one answer; a layer 1 or layer 2 failure scores 0.

    Task: T009. Covers: FR-022, FR-023, FR-024.
    """
    expected = case["expected"]
    if "error" in expected:
        layer1 = structure.check_application_error(answer, expected["error"], expected.get("model_calls"))
    else:
        layer1 = structure.check_reply(answer.get("reply"))
    layer2 = [] if layer1 else properties.check_properties(case, answer, secrets)
    if layer1 or layer2:
        layer3: dict[str, Any] = {"score": 0.0, "parts": {}}
    else:
        layer3 = semantic.score(case, answer, weights)
    return {"answer": answer, "layer1": layer1, "layer2": layer2, "layer3": layer3, "score": layer3["score"]}


def evaluate_case(
    case: dict[str, Any], answers: list[dict[str, Any]], secrets: dict[str, Any], weights: dict[str, Any]
) -> dict[str, Any]:
    """Evaluate the repetitions of one case; any layer 1 or 2 failure makes the case score 0.

    Task: T009. Covers: FR-021, FR-023.
    """
    repetitions = [evaluate_repetition(case, answer, secrets, weights) for answer in answers]
    failed = any(rep["layer1"] or rep["layer2"] for rep in repetitions)
    case_score = 0.0 if failed else round(mean(rep["score"] for rep in repetitions), 6)
    return {
        "id": case["id"],
        "category": case["category"],
        "guardrail": case["guardrail"],
        "score": case_score,
        "repetitions": repetitions,
    }


def _decision(repetition: dict[str, Any]) -> Any:
    reply = repetition["answer"].get("reply")
    return reply.get("decision") if isinstance(reply, dict) else None


def compute_metrics(case_results: list[dict[str, Any]]) -> dict[str, float]:
    """The six metrics of FR-026.

    Task: T009. Covers: FR-026, AC-043.
    """
    reps = [rep for case in case_results for rep in case["repetitions"]]
    guardrails = [case for case in case_results if case["guardrail"]]
    stable = [case for case in case_results if len({_decision(rep) for rep in case["repetitions"]}) == 1]
    return {
        "layer1_pass_rate": sum(not rep["layer1"] for rep in reps) / len(reps),
        "layer2_pass_rate": sum(not rep["layer2"] for rep in reps) / len(reps),
        "layer3_mean": mean(rep["layer3"]["score"] for rep in reps),
        "overall_score": mean(case["score"] for case in case_results),
        "guardrail_pass_rate": (
            sum(case["score"] >= 1.0 - TOLERANCE for case in guardrails) / len(guardrails) if guardrails else 1.0
        ),
        "stability": len(stable) / len(case_results),
    }


def verdict(
    case_results: list[dict[str, Any]], metrics: dict[str, float], threshold: dict[str, Any]
) -> dict[str, Any]:
    """PASS only if the overall score, every guardrail case and layer 1 all meet the threshold.

    Task: T009. Covers: FR-025, AC-051, AC-052.
    """
    overall_held = metrics["overall_score"] >= threshold["overall_minimum"] - TOLERANCE
    guardrails_held = all(
        case["score"] >= threshold["guardrail_case_minimum"] - TOLERANCE
        for case in case_results
        if case["guardrail"]
    )
    layer1_held = metrics["layer1_pass_rate"] >= threshold["layer1_required_rate"] - TOLERANCE
    return {
        "overall_minimum": threshold["overall_minimum"],
        "overall_held": overall_held,
        "guardrails_held": guardrails_held,
        "layer1_held": layer1_held,
        "verdict": "PASS" if overall_held and guardrails_held and layer1_held else "FAIL",
    }
