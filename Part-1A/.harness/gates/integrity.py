"""Integrity gate: protected files, the test count and forbidden markers, against the baseline tag."""

from __future__ import annotations

import ast
import re

from common import GateResult, GateRun, failure, gate_main, python_files, repo_root

TAG = "baseline-before-implement"
PROTECTED = ("tests", "specs", ".harness", ".specify/memory/constitution.md", "pyproject.toml")
TASKS = "specs/001-lcgkit-toolkit/tasks.md"
FORBIDDEN = re.compile(
    r"(pytest|unittest)\.(mark\.)?(skip|skipif|xfail)\b|importorskip|\bxfail\b|noqa|nosec"
    r"|type:\s*ignore"
)
CHECKBOX = re.compile(r"\[[xX]\]")
TEST_COUNT = re.compile(r"test_functions=(\d+)")


def git(gate: GateRun, *args: str) -> tuple[int, str]:
    """Run a git command in Part-1A and return (exit status, stdout)."""
    status, out, _ = gate.run(["git", *args])
    return status, out


def count_tests() -> int:
    """Count `def test_*` functions under tests/, statically."""
    total = 0
    for path in python_files(repo_root() / "tests"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
                "test_"
            ):
                total += 1
    return total


def changed_protected(gate: GateRun) -> list[dict[str, object]]:
    """Return a failure for every protected file that differs from the tag."""
    _, changed = git(gate, "diff", "--name-only", "--relative", TAG, "--", *PROTECTED)
    _, added = git(gate, "ls-files", "--others", "--exclude-standard", "--", *PROTECTED)
    failures = []
    for path in sorted({*changed.split(), *added.split()}):
        if path == TASKS and tasks_only_ticked(gate):
            continue
        failures.append(failure("protected-path-changed", f"{path} equals the baseline",
                                f"{path} differs from tag {TAG}", []))
    return failures


def tasks_only_ticked(gate: GateRun) -> bool:
    """True if tasks.md differs from the tag only in its checkboxes."""
    status, old = git(gate, "show", f"{TAG}:./{TASKS}")
    new = (repo_root() / TASKS).read_text()
    return status == 0 and CHECKBOX.sub("[ ]", old) == CHECKBOX.sub("[ ]", new)


def added_lines(gate: GateRun) -> list[tuple[str, str]]:
    """Return (file, line) for every line added under src/ or tests/ since the tag."""
    _, diff = git(gate, "diff", "-U0", "--relative", TAG, "--", "src", "tests")
    lines, current = [], ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            lines.append((current, line[1:]))
    _, fresh = git(gate, "ls-files", "--others", "--exclude-standard", "--", "src", "tests")
    for name in fresh.split():
        lines += [(name, text) for text in (repo_root() / name).read_text().splitlines()]
    return lines


def forbidden_markers(gate: GateRun) -> list[dict[str, object]]:
    """Return a failure for each added skip, xfail, noqa, nosec or type-ignore."""
    return [
        failure("forbidden-marker", "no suppression or skip added", f"{name}: {text.strip()}", [])
        for name, text in added_lines(gate)
        if FORBIDDEN.search(text)
    ]


def random_imports() -> list[dict[str, object]]:
    """Return a failure for each file under src/ that imports the `random` module."""
    failures = []
    for path in python_files(repo_root() / "src"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            if "random" in names:
                failures.append(failure("random-import", "no import of random under src/",
                                        f"{path.relative_to(repo_root())}:{node.lineno}", []))
    return failures


def run(gate: GateRun) -> GateResult:
    """Run every integrity check; a missing tag or annotation fails."""
    status, _ = git(gate, "rev-parse", "-q", "--verify", f"refs/tags/{TAG}")
    if status != 0:
        return gate.finish([failure("baseline-tag", f"tag {TAG} exists",
                                    f'create it: git tag -a {TAG} -m "test_functions=<N>"', [])])
    _, note = git(gate, "tag", "-l", "--format=%(contents)", TAG)
    match = TEST_COUNT.search(note)
    failures = changed_protected(gate) + forbidden_markers(gate) + random_imports()
    if not match:
        failures.append(failure("baseline-annotation", "test_functions=<N> in the tag message",
                                note.strip() or "empty annotation", []))
    elif count_tests() < int(match.group(1)):
        failures.append(failure("test-count", f"at least {match.group(1)} test functions",
                                f"{count_tests()} found", []))
    return gate.finish(failures)


if __name__ == "__main__":
    gate_main("integrity", run)
