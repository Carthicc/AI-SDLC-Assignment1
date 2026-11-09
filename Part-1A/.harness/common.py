"""Shared helpers for the harness runner and the gates. Imports nothing from src/lcgkit."""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
TAIL_LINES = 200
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
EXIT_NOT_RUNNABLE = 127
EXIT_TIMEOUT = 124
DEFAULT_TIMEOUT = 900
MARKER_NAMES = ("ac", "fr")


@dataclass
class GateResult:
    """Outcome of one gate; stored in results.json."""

    name: str
    status: str
    command: str
    exit_status: int
    duration_seconds: float
    stdout_path: str
    stderr_path: str
    failures: list[dict[str, object]] = field(default_factory=list)


def repo_root() -> Path:
    """Return the Part-1A folder, which holds src/, tests/ and evidence/."""
    return HARNESS_DIR.parent


def git_root() -> Path:
    """Return the top folder of the Git repository that contains Part-1A."""
    done = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=repo_root(), capture_output=True, text=True, check=True,
    )
    return Path(done.stdout.strip())


def new_run_folder(run_id: str) -> Path:
    """Create and return evidence/harness-results/<run-id>/."""
    folder = repo_root() / "evidence" / "harness-results" / run_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def tool(name: str) -> str:
    """Return the path of a tool installed next to the running Python, else its bare name."""
    candidate = Path(sys.executable).parent / name
    return str(candidate) if candidate.exists() else name


def last_lines(text: str, count: int = TAIL_LINES) -> str:
    """Return the last `count` lines of `text`."""
    return "\n".join(text.splitlines()[-count:])


class GateRun:
    """Runs the commands of one gate and records their output in the run folder."""

    def __init__(self, name: str, folder: Path) -> None:
        """Start a gate called `name` that writes into `folder`."""
        self.name = name
        self.folder = folder
        self.commands: list[str] = []
        self.exit_status = 0
        self.started = time.perf_counter()
        self.stdout_file = folder / f"{name}.stdout.txt"
        self.stderr_file = folder / f"{name}.stderr.txt"
        self.stdout_file.write_text("")
        self.stderr_file.write_text("")

    def note(self, text: str) -> None:
        """Append a line to the gate's standard-output file (for gates that run no tool)."""
        with self.stdout_file.open("a") as handle:
            handle.write(text + "\n")

    def run(
        self, command: list[str], cwd: Path | None = None, timeout: int = DEFAULT_TIMEOUT
    ) -> tuple[int, str, str]:
        """Run `command`; return (exit status, stdout, stderr). A missing tool gives 127."""
        text = " ".join(command)
        self.commands.append(text)
        try:
            done = subprocess.run(
                command, cwd=cwd or repo_root(), capture_output=True, text=True, timeout=timeout,
            )
            status, out, err = done.returncode, done.stdout, done.stderr
        except FileNotFoundError as exc:
            status, out, err = EXIT_NOT_RUNNABLE, "", f"cannot run {command[0]}: {exc}"
        except subprocess.TimeoutExpired:
            status, out, err = EXIT_TIMEOUT, "", f"timed out after {timeout} s: {text}"
        with self.stdout_file.open("a") as handle:
            handle.write(f"$ {text}\n{out}\n")
        with self.stderr_file.open("a") as handle:
            handle.write(f"$ {text}\n{err}\n")
        if status != 0 and self.exit_status == 0:
            self.exit_status = status
        return status, out, err

    def finish(
        self, failures: list[dict[str, object]], ok_exits: tuple[int, ...] = (0,)
    ) -> GateResult:
        """Build the result: FAIL on any failure, or on an exit status the gate did not accept."""
        if not failures and self.exit_status not in ok_exits:
            tail = last_lines(self.stderr_file.read_text() + self.stdout_file.read_text(), 20)
            failures = [failure("tool", "the tool runs and reports no problem", tail, [])]
        elapsed = round(time.perf_counter() - self.started, 2)
        return GateResult(
            name=self.name,
            status=STATUS_FAIL if failures else STATUS_PASS,
            command=" && ".join(self.commands) or "built-in check",
            exit_status=self.exit_status,
            duration_seconds=elapsed,
            stdout_path=self.stdout_file.name,
            stderr_path=self.stderr_file.name,
            failures=failures,
        )


def failure(rule: str, expected: str, observed: str, ids: list[str]) -> dict[str, object]:
    """Build one failure entry."""
    return {"rule_or_test": rule, "expected": expected, "observed": observed, "ids": ids}


def gate_main(name: str, run: Callable[[GateRun], GateResult]) -> None:
    """Entry point of a gate script: parse --folder, run the gate, write <name>.result.json."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True, type=Path)
    args = parser.parse_args()
    result = run(GateRun(name, args.folder))
    (args.folder / f"{name}.result.json").write_text(json.dumps(asdict(result), indent=2))


def python_files(folder: Path) -> list[Path]:
    """Return the .py files under `folder`, sorted."""
    return sorted(folder.rglob("*.py")) if folder.exists() else []


def marker_ids(tree: ast.AST) -> list[str]:
    """Return every ID given to an ac(...) or fr(...) marker anywhere in `tree`."""
    found: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in MARKER_NAMES
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            found.append(node.args[0].value)
    return found


def test_marker_map(tests_dir: Path) -> dict[str, list[str]]:
    """Map 'relative/path.py::function' to the marker IDs that apply to that test."""
    mapping: dict[str, list[str]] = {}
    root = repo_root()
    for path in python_files(tests_dir):
        tree = ast.parse(path.read_text())
        module_ids = [
            i for node in tree.body if isinstance(node, ast.Assign) for i in marker_ids(node)
        ]
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
                "test_"
            ):
                own = [i for dec in node.decorator_list for i in marker_ids(dec)]
                mapping[f"{path.relative_to(root)}::{node.name}"] = module_ids + own
    return mapping


def junit_failures(xml_path: Path) -> list[dict[str, object]]:
    """Read a pytest junit file; return one failure per failed or errored test, with its IDs."""
    if not xml_path.exists():
        return []
    markers = test_marker_map(repo_root() / "tests")
    entries = []
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        problem = case.find("failure") if case.find("failure") is not None else case.find("error")
        if problem is None:
            continue
        parts = case.get("classname", "").split(".")
        name = (case.get("name") or "").split("[")[0]
        ids: list[str] = []
        for cut in range(len(parts), 0, -1):
            module = "/".join(parts[:cut]) + ".py"
            if (repo_root() / module).exists():
                ids = markers.get(f"{module}::{name}", [])
                break
        message = (problem.get("message") or "")[:1000]
        entries.append(
            failure(f"{case.get('classname')}::{case.get('name')}", "the test passes", message, ids)
        )
    return entries
