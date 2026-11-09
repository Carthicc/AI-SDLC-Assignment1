"""Protected files, counts and forbidden markers, compared with the baseline tag (task T014)."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

TAG = "baseline-1b-before-implement"
PROTECTED = ("tests", "evals", "specs", ".harness", ".specify/memory/constitution.md", "pyproject.toml")
TASKS = "specs/001-lcgkit-assistant/tasks.md"
FORBIDDEN = re.compile(
    r"(pytest|unittest)\.(mark\.)?(skip|skipif|xfail)\b|importorskip|\bxfail\b|noqa|nosec|type:\s*ignore"
)
CHECKBOX = re.compile(r"\[[xX]\]")
ANNOTATION = re.compile(r"test_functions=(\d+)\s+dataset_cases=(\d+)")


def _git(root: Path, *args: str) -> tuple[int, str]:
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    return done.returncode, done.stdout


def _problem(rule: str, detail: str) -> dict[str, str]:
    return {"rule": rule, "detail": detail}


def count_tests(root: Path) -> int:
    """Count `def test_` functions under tests/, statically."""
    total = 0
    for path in sorted((root / "tests").rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test_"):
                total += 1
    return total


def count_cases(root: Path) -> int:
    """The number of cases in evals/dataset.json (0 when the file is missing)."""
    path = root / "evals" / "dataset.json"
    return len(json.loads(path.read_text()).get("cases", [])) if path.exists() else 0


def _tasks_only_ticked(root: Path) -> bool:
    status, old = _git(root, "show", f"{TAG}:./{TASKS}")
    new = (root / TASKS).read_text()
    return status == 0 and CHECKBOX.sub("[ ]", old) == CHECKBOX.sub("[ ]", new)


def _changed_files(root: Path) -> list[dict[str, str]]:
    _, changed = _git(root, "diff", "--name-only", "--relative", TAG, "--", *PROTECTED)
    _, added = _git(root, "ls-files", "--others", "--exclude-standard", "--", *PROTECTED)
    found = []
    for path in sorted({*changed.split(), *added.split()}):
        if path == TASKS and _tasks_only_ticked(root):
            continue
        found.append(_problem("protected-path-changed", f"{path} differs from tag {TAG}"))
    return found


def _added_lines(root: Path) -> list[tuple[str, str]]:
    _, diff = _git(root, "diff", "-U0", "--relative", TAG, "--", "src", "tests")
    lines, current = [], ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            lines.append((current, line[1:]))
    _, fresh = _git(root, "ls-files", "--others", "--exclude-standard", "--", "src", "tests")
    for name in fresh.split():
        lines += [(name, text) for text in (root / name).read_text().splitlines()]
    return lines


def check(root: Path) -> list[dict[str, Any]]:
    """Return the integrity problems (empty means the check passes).

    Task: T014. Covers: FR-030, Constitution V.
    """
    status, _ = _git(root, "rev-parse", "-q", "--verify", f"refs/tags/{TAG}")
    if status != 0:
        return [_problem("baseline-tag", f'tag {TAG} is missing; create it with git tag -a {TAG} -m "test_functions=<N> dataset_cases=<M>"')]
    _, note = _git(root, "tag", "-l", "--format=%(contents)", TAG)
    match = ANNOTATION.search(note)
    problems = _changed_files(root)
    problems += [
        _problem("forbidden-marker", f"{name}: {text.strip()}")
        for name, text in _added_lines(root)
        if FORBIDDEN.search(text)
    ]
    if not match:
        return problems + [_problem("baseline-annotation", "the tag message needs test_functions=<N> dataset_cases=<M>")]
    if count_tests(root) < int(match.group(1)):
        problems.append(_problem("test-count", f"fewer than {match.group(1)} test functions"))
    if count_cases(root) < int(match.group(2)):
        problems.append(_problem("case-count", f"fewer than {match.group(2)} dataset cases"))
    return problems
