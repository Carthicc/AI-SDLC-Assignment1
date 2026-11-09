"""The results and feedback files."""

import json
from pathlib import Path

import pytest
import report
import scoring

from tests.conftest import MARKER, call_reply, clarify_reply

THRESHOLD = json.loads((Path(__file__).parents[2] / ".harness" / "threshold.json").read_text())
SCHEMA = json.loads(
    (
        Path(__file__).parents[2]
        / "specs"
        / "001-lcgkit-assistant"
        / "contracts"
        / "eval-results.schema.json"
    ).read_text()
)
KEY = "FAKE-KEY-0123456789"
INFO = {
    "model": "gemini-3.5-flash-lite",
    "settings": {"temperature": 0, "response_format": "application/json"},
    "prompt_sha256": "a" * 64,
}


def make_case(case_id, expected=None):
    expected = expected or {"decision": "clarify", "missing": ["seed"]}
    return {
        "id": case_id,
        "category": "missing-information",
        "text": "t",
        "guardrail": False,
        "covers": [],
        "expected": expected,
    }


def results_for(cases, answers):
    return [
        scoring.evaluate_case(c, a, {"key": KEY, "marker": MARKER}, THRESHOLD["weights"])
        for c, a in zip(cases, answers, strict=True)
    ]


def good():
    return {"reply": clarify_reply(), "model_calls": 1}


def build(cases, answers, seconds=12.34):
    results = results_for(cases, answers)
    metrics = scoring.compute_metrics(results)
    verdict = scoring.verdict(results, metrics, THRESHOLD)
    return results, report.build_report(
        "run-1", INFO, results, metrics, THRESHOLD, verdict, seconds
    )


@pytest.mark.ac("AC-045")
@pytest.mark.fr("FR-025")
def test_the_report_has_the_fields_of_the_schema():
    _, built = build([make_case("A")], [[good()] * 3])
    assert set(SCHEMA["required"]) <= set(built)
    assert built["model"] == "gemini-3.5-flash-lite"
    assert built["prompt_sha256"] == "a" * 64
    assert built["duration_seconds"] == 12.3
    assert built["verdict"] == "PASS"
    assert set(built["metrics"]) >= {"overall_score", "stability", "guardrail_pass_rate"}
    assert built["threshold"]["overall_minimum"] == 0.85


@pytest.mark.ac("AC-045")
def test_large_results_are_stored_as_a_hash_and_small_ones_kept():
    small = {"reply": call_reply(), "result": {"outputs": ["1"]}, "model_calls": 1}
    large = {"reply": call_reply(), "result": {"outputs": ["1234567"] * 5000}, "model_calls": 1}
    assert report.summarise_answer(small)["result"] == {"outputs": ["1"]}
    summary = report.summarise_answer(large)["result"]
    assert set(summary) == {"sha256", "bytes"}
    assert summary["bytes"] > 10_000


@pytest.mark.ac("AC-046")
@pytest.mark.fr("FR-027")
def test_feedback_lists_each_failed_case():
    cases = [make_case("A"), make_case("B")]
    wrong = {"reply": clarify_reply(missing=[]), "model_calls": 1}
    results, _ = build(cases, [[good()] * 3, [wrong] * 3])
    feedback = report.build_feedback(results, cases)
    assert [f["case"]["id"] for f in feedback["failed_cases"]] == ["B"]
    first = feedback["failed_cases"][0]["repetitions"][0]
    assert first["layer2"][0]["rule"] == "PROP-09"
    assert first["answer"] == wrong
    assert report.build_feedback(results[:1], cases[:1]) == {"failed_cases": []}


@pytest.mark.ac("AC-045")
def test_write_run_writes_the_folder_and_the_latest_copy(tmp_path):
    results, built = build([make_case("A")], [[good()] * 3])
    (tmp_path / "evidence").mkdir()
    folder = report.write_run(tmp_path, "run-1", built, report.build_feedback(results, []), KEY)
    assert (folder / "eval-results.json").exists()
    assert not (folder / "feedback.json").exists()
    assert (tmp_path / "evidence" / "eval-results.json").read_text() == (
        folder / "eval-results.json"
    ).read_text()


@pytest.mark.ac("AC-054")
def test_write_run_refuses_to_write_the_key(tmp_path):
    leaky = {"reply": clarify_reply(f"the key is {KEY}"), "model_calls": 1}
    _, built = build([make_case("A")], [[leaky] * 3])
    (tmp_path / "evidence").mkdir()
    with pytest.raises(ValueError, match="API key"):
        report.write_run(tmp_path, "run-1", built, {"failed_cases": []}, KEY)
    assert not (tmp_path / "evidence" / "eval-runs").exists()
