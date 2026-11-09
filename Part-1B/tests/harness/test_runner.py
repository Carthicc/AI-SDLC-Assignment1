"""The runner, with a fake application and the pre-checks replaced by an injected function."""

import json
import shlex
import shutil
import sys
from pathlib import Path

import pytest
import run_eval
from fakes import fake_app

HARNESS = Path(__file__).parents[2] / ".harness"
APP = shlex.join([sys.executable, str(HARNESS / "fakes" / "fake_app.py")])
KEY = "FAKE-KEY-0123456789"
PASSING = [{"name": "lint", "status": "PASS", "output_tail": ""}]
CASES = [
    {
        "id": "S1",
        "category": "normal",
        "text": fake_app.CALL_TEXT,
        "guardrail": False,
        "covers": [],
        "expected": {
            "decision": "call",
            "operation": "sequence",
            "arguments": fake_app.CALL_ARGUMENTS,
        },
    },
    {
        "id": "S2",
        "category": "missing-information",
        "text": fake_app.CLARIFY_TEXT,
        "guardrail": False,
        "covers": [],
        "expected": {"decision": "clarify", "missing": ["seed"]},
    },
    {
        "id": "S3",
        "category": "adversarial",
        "text": fake_app.REFUSE_TEXT,
        "guardrail": True,
        "covers": [],
        "expected": {"decision": "refuse", "reason": "insecure-purpose"},
    },
    {
        "id": "S4",
        "category": "malformed",
        "text": "",
        "guardrail": False,
        "covers": [],
        "expected": {"decision": "clarify", "model_calls": 0},
    },
]


@pytest.fixture(name="root")
def root_fixture(tmp_path, monkeypatch):
    (tmp_path / ".harness").mkdir()
    shutil.copy(HARNESS / "threshold.json", tmp_path / ".harness" / "threshold.json")
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals" / "dataset.json").write_text(
        json.dumps({"cases": CASES, "covered_elsewhere": {}})
    )
    (tmp_path / "evidence").mkdir()
    monkeypatch.setattr(run_eval.dataset, "validate", lambda *_: [])
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    monkeypatch.setenv("FAKE_COUNT_FILE", str(tmp_path / "count.txt"))
    return tmp_path


def run(root, *extra, prechecks=lambda _root: PASSING):
    pauses = []
    argv = ["--root", str(root), "--app", APP, "--run-id", "r1", *extra]
    status = run_eval.main(argv, prechecks_fn=prechecks, sleep=pauses.append)
    return status, pauses


@pytest.mark.ac("AC-044")
@pytest.mark.fr("FR-025")
def test_a_good_application_passes(root, capsys, monkeypatch):
    monkeypatch.setenv("FAKE_MODE", "good")
    status, _ = run(root)
    assert status == 0
    assert capsys.readouterr().out.strip().endswith("PASS")
    assert (root / "evidence" / "eval-runs" / "r1" / "eval-results.json").exists()
    assert (root / "evidence" / "eval-results.json").exists()


@pytest.mark.fr("FR-021")
def test_every_case_runs_three_times_and_no_pause_follows_a_run_without_a_model_call(
    root, monkeypatch
):
    monkeypatch.setenv("FAKE_MODE", "good")
    _, pauses = run(root)
    assert (root / "count.txt").read_text().count("x") == 12
    assert len(pauses) == 9
    assert set(pauses) == {3}


@pytest.mark.ac("AC-047")
def test_an_application_that_gives_no_answer_fails_every_case(root, capsys, monkeypatch):
    monkeypatch.setenv("FAKE_MODE", "no-answer")
    status, _ = run(root)
    assert status == 1
    assert capsys.readouterr().out.strip().endswith("FAIL")
    report = json.loads((root / "evidence" / "eval-results.json").read_text())
    assert len(report["cases"]) == len(CASES)
    assert all(case["score"] == 0 for case in report["cases"])


@pytest.mark.ac("AC-058")
@pytest.mark.fr("FR-030")
def test_a_failed_precheck_stops_before_the_application_starts(root, capsys, monkeypatch):
    monkeypatch.setenv("FAKE_MODE", "good")
    failing = [{"name": "lint", "status": "FAIL", "output_tail": "x"}]
    status, _ = run(root, prechecks=lambda _root: failing)
    assert status == 1
    assert capsys.readouterr().out.strip().endswith("FAIL")
    assert not (root / "count.txt").exists()
    assert not (root / "evidence" / "eval-results.json").exists()


@pytest.mark.fr("FR-025")
def test_a_partial_run_is_never_a_pass_and_writes_no_latest_copy(root, capsys, monkeypatch):
    monkeypatch.setenv("FAKE_MODE", "good")
    status, _ = run(root, "--only", "S1")
    assert status == 1
    assert capsys.readouterr().out.strip().endswith("PARTIAL")
    assert not (root / "evidence" / "eval-results.json").exists()
    assert (root / "evidence" / "eval-runs" / "r1" / "eval-results.json").exists()


@pytest.mark.fr("FR-025")
def test_the_results_hold_the_duration_and_not_the_key(root, monkeypatch):
    monkeypatch.setenv("FAKE_MODE", "good")
    run(root)
    text = (root / "evidence" / "eval-results.json").read_text()
    assert "duration_seconds" in json.loads(text)
    assert KEY not in text


@pytest.mark.fr("FR-030")
def test_a_leaked_key_stops_the_report_from_being_written(root, monkeypatch):
    monkeypatch.setenv("FAKE_MODE", "leaks-key")
    with pytest.raises(ValueError, match="API key"):
        run(root)
    assert not (root / "evidence" / "eval-results.json").exists()
