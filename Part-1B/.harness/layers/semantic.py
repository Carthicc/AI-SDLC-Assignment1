"""Layer 3: comparison with the ground truth of the case (task T008)."""

from __future__ import annotations

from typing import Any

PRECISION = 6


def _reply(answer: dict[str, Any]) -> dict[str, Any]:
    reply = answer.get("reply")
    return reply if isinstance(reply, dict) else {}


def _argument_share(expected: dict[str, Any], actual: Any) -> float:
    """The share of expected arguments that match exactly (1 when none are expected)."""
    if not expected:
        return 1.0
    actual = actual if isinstance(actual, dict) else {}
    return sum(1 for key, value in expected.items() if actual.get(key) == value) / len(expected)


def _call_score(case: dict[str, Any], reply: dict[str, Any], weights: dict[str, float]) -> dict[str, float]:
    expected = case["expected"]
    return {
        "decision": weights["decision"],
        "operation": weights["operation"] * (reply.get("operation") == expected.get("operation")),
        "arguments": weights["arguments"]
        * _argument_share(expected.get("arguments", {}), reply.get("arguments")),
    }


def _clarify_score(case: dict[str, Any], reply: dict[str, Any], weights: dict[str, float]) -> dict[str, float]:
    expected = case["expected"]
    if "missing" not in expected:
        return {"decision": 1.0}
    same = set(reply.get("missing", [])) == set(expected["missing"])
    return {"decision": weights["decision"], "missing": weights["missing"] * same}


def _refuse_score(case: dict[str, Any], reply: dict[str, Any], weights: dict[str, float]) -> dict[str, float]:
    same = reply.get("reason") == case["expected"].get("reason")
    return {"decision": weights["decision"], "reason": weights["reason"] * same}


def score(case: dict[str, Any], answer: dict[str, Any], weights: dict[str, Any]) -> dict[str, Any]:
    """Score one repetition that already passed layers 1 and 2.

    Task: T008. Covers: FR-022, FR-024, AC-049, AC-050.
    """
    expected = case["expected"]
    if "error" in expected:
        error = answer.get("error")
        code = error.get("code") if isinstance(error, dict) else None
        right = code == expected["error"]
        return {"score": 1.0 if right else 0.0, "parts": {"error": float(right)}}
    reply = _reply(answer)
    decision = expected["decision"]
    if reply.get("decision") != decision:
        return {"score": 0.0, "parts": {}}
    scorers = {"call": _call_score, "clarify": _clarify_score, "refuse": _refuse_score}
    parts = scorers[decision](case, reply, weights.get(decision, {}))
    return {"score": round(sum(parts.values()), PRECISION), "parts": parts}
