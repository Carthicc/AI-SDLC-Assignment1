"""Shows that every gate can fail: one bad input and one clean sample per gate.

Usage: uv run python .harness/selfcheck.py
Builds throw-away projects in a temporary folder (nothing is written to this repository, and the
secret-like string is assembled at run time inside a temporary Git repository). Imports nothing
from src/lcgkit.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from common import HARNESS_DIR, STATUS_FAIL, STATUS_PASS

GIT = ["git", "-c", "user.name=selfcheck", "-c", "user.email=selfcheck@invalid.invalid"]
PYPROJECT = (HARNESS_DIR.parent / "pyproject.toml").read_text()
OK_MODULE = '"""A clean module."""\n\n\ndef double(value: int) -> int:\n    """Return twice `value`."""\n    return value * 2\n'
SPEC = "# Spec\n\n- **FR-001** The thing works.\n\n| ID | Acceptance criterion | Requirement |\n|---|---|---|\n| AC-001 | It works | FR-001 |\n"
MARKED_TEST = 'import pytest\n\nfrom lcgkit.ok import double\n\n\n@pytest.mark.ac("AC-001")\n@pytest.mark.fr("FR-001")\ndef test_double() -> None:\n    assert double(2) == 4\n'
TWO_TESTS = "def test_a() -> None:\n    assert True\n\n\ndef test_b() -> None:\n    assert True\n"
LONG_FUNCTION = '"""Long."""\n\n\ndef long_one() -> int:\n    """Too long."""\n    total = 0\n' + "    total += 1\n" * 40 + "    return total\n"
SECRET_PARTS = ("AKIA", "Y3VQ4CIPXERUMIFQ")
CORE = '"""Core."""\n\n\ndef add(left: int, right: int) -> int:\n    """Add."""\n    return left + right\n'


@dataclass
class Case:
    """One gate, its bad input, the rule it must report, and the clean sample."""

    gate: str
    bad_input: str
    expected_rule: str
    bad: dict[str, str]
    clean: dict[str, str]
    tag: str | None = None
    edit_after_tag: dict[str, str] | None = None


def base(**extra: str) -> dict[str, str]:
    """Files every sample project has."""
    files = {
        "src/lcgkit/__init__.py": '"""Package."""\n',
        "src/lcgkit/ok.py": OK_MODULE,
        "tests/__init__.py": "",
        "tests/test_ok.py": MARKED_TEST,
        "specs/001-lcgkit-toolkit/spec.md": SPEC,
        ".gitignore": "__pycache__/\n.venv/\nmutants/\nevidence/\n",
    }
    files.update(extra)
    return files


def audit_project(version: str) -> str:
    """A bare project that depends on one pinned version of urllib3."""
    return f'[project]\nname = "sample"\nversion = "0"\nrequires-python = ">=3.12"\ndependencies = ["urllib3=={version}"]\n'


def cases() -> list[Case]:
    """The cases, one or more per gate."""
    secret = "aws_key = '" + "".join(SECRET_PARTS) + "'\n"
    return [
        Case("lint", "an unused import (Ruff F401)", "F401",
             base(**{"src/lcgkit/bad.py": '"""Bad."""\n\nimport os\n'}), base()),
        Case("length", "a 41-line function", "function-length",
             base(**{"src/lcgkit/long.py": LONG_FUNCTION}), base()),
        Case("types", "a wrong return type (mypy)", "mypy",
             base(**{"src/lcgkit/bad.py": '"""Bad."""\n\n\ndef f(x: int) -> str:\n    """Bad."""\n    return x\n'}),
             base()),
        Case("security", "pickle.loads (Bandit B301, medium)", "B301",
             base(**{"src/lcgkit/bad.py": '"""Bad."""\nimport pickle\n\n\ndef f(data: bytes) -> object:\n    """Bad."""\n    return pickle.loads(data)\n'}),
             base()),
        Case("secrets", "an AWS-style key, written at run time", "aws-access-token",
             base(**{"src/lcgkit/key.py": '"""Key."""\n' + secret}), base()),
        Case("tests", "a failing test", "test_bad",
             base(**{"tests/test_bad.py": "def test_bad() -> None:\n    assert 1 == 2\n"}), base()),
        Case("integrity", "a test function removed after the tag", "test-count",
             base(**{"tests/test_two.py": TWO_TESTS}), base(**{"tests/test_two.py": TWO_TESTS}),
             tag="test_functions=3", edit_after_tag={"tests/test_two.py": "def test_a() -> None:\n    assert True\n"}),
        Case("traceability", "an acceptance criterion with no test", "untested-id",
             base(**{"tests/test_ok.py": "def test_double() -> None:\n    assert True\n"}), base()),
        Case("audit", "urllib3 1.25.0, which has known vulnerabilities", "PYSEC",
             {"pyproject.toml": audit_project("1.25.0")}, {"pyproject.toml": audit_project("2.8.0")}),
        Case("mutation", "a test that asserts nothing useful", "mutation-score",
             {"src/lcgkit/__init__.py": '"""P."""\n', "src/lcgkit/core/__init__.py": '"""C."""\n',
              "src/lcgkit/core/calc.py": CORE, "tests/__init__.py": "",
              "tests/test_calc.py": "from lcgkit.core.calc import add\n\n\ndef test_add() -> None:\n    assert add(1, 2) is not None\n",
              ".gitignore": "__pycache__/\nmutants/\nevidence/\n"},
             {"src/lcgkit/__init__.py": '"""P."""\n', "src/lcgkit/core/__init__.py": '"""C."""\n',
              "src/lcgkit/core/calc.py": CORE, "tests/__init__.py": "",
              "tests/test_calc.py": "from lcgkit.core.calc import add\n\n\ndef test_add() -> None:\n    assert add(1, 2) == 3\n    assert add(5, 7) == 12\n    assert add(0, 0) == 0\n",
              ".gitignore": "__pycache__/\nmutants/\nevidence/\n"}),
    ]


def build(files: dict[str, str], tag: str | None, edits: dict[str, str] | None, where: Path) -> None:
    """Create a project folder with its own Git repository (and tag, if asked)."""
    shutil.copytree(HARNESS_DIR, where / ".harness",
                    ignore=shutil.ignore_patterns("__pycache__", "selfcheck.py"))
    (where / "pyproject.toml").write_text(PYPROJECT)
    for name, text in files.items():
        target = where / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    if "pyproject.toml" in files:
        subprocess.run(["uv", "lock", "-q"], cwd=where, check=True, capture_output=True)
    for command in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "sample"]):
        subprocess.run([*GIT, *command], cwd=where, check=True, capture_output=True)
    if tag:
        subprocess.run([*GIT, "tag", "-a", "baseline-before-implement", "-m", tag],
                       cwd=where, check=True, capture_output=True)
    for name, text in (edits or {}).items():
        (where / name).write_text(text)


def run_gate(gate: str, where: Path) -> dict[str, object]:
    """Run one gate script in the sample project and return its result."""
    folder = where / "evidence" / "harness-results" / "selfcheck"
    folder.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(where / ".harness"), "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run([sys.executable, "-m", f"gates.{gate}", "--folder", str(folder)],
                   cwd=where, env=env, capture_output=True, text=True, timeout=900, check=False)
    return json.loads((folder / f"{gate}.result.json").read_text())


def check(case: Case) -> tuple[str, str]:
    """Return (bad-input outcome, clean-sample outcome) for one case."""
    outcomes = []
    for files in (case.bad, case.clean):
        with tempfile.TemporaryDirectory() as tmp:
            build(files, case.tag, case.edit_after_tag if files is case.bad else None, Path(tmp))
            result = run_gate(case.gate, Path(tmp))
        rules = [str(f["rule_or_test"]) for f in result["failures"]]
        outcomes.append((result["status"], rules))
    (bad_status, bad_rules), (clean_status, _) = outcomes
    bad_ok = bad_status == STATUS_FAIL and any(case.expected_rule in r for r in bad_rules)
    clean_ok = clean_status == STATUS_PASS
    return ("FAIL as expected" if bad_ok else f"WRONG ({bad_status}: {bad_rules[:3]})",
            "PASS as expected" if clean_ok else f"WRONG ({clean_status})")


def main() -> int:
    """Run every case, print a table, and exit 0 only if every gate behaved as expected."""
    all_good = True
    print(f"{'gate':<13} {'bad input':<44} {'bad sample':<20} clean sample")
    for case in cases():
        bad, clean = check(case)
        all_good &= bad.endswith("expected") and clean.endswith("expected")
        print(f"{case.gate:<13} {case.bad_input:<44} {bad:<20} {clean}")
    print("not self-checked (needs the finished service): contract")
    print("SELFCHECK PASS" if all_good else "SELFCHECK FAIL")
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
