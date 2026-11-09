"""The checks on the application code that run before any model call (task T013)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import integrity

CONFIG = Path(__file__).resolve().parent / "config" / "gitleaks.toml"
TAIL_LINES = 20
MISSING_GITLEAKS = "install gitleaks: brew install gitleaks"


def _tool(name: str) -> str:
    candidate = Path(sys.executable).parent / name
    return str(candidate) if candidate.exists() else name


def _git_root(root: Path) -> Path:
    done = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True, check=True
    )
    return Path(done.stdout.strip())


def env_is_ignored(root: Path) -> bool:
    """True when Git ignores a `.env` file in `root`.

    Task: T013. Covers: FR-015, SC-006.
    """
    done = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=root, check=False)
    return done.returncode == 0


def tracked_copy(root: Path) -> Path:
    """Copy the files that Git tracks or could track (not the ignored ones) into a temporary folder.

    Task: T013. Covers: FR-030, SC-006.
    """
    done = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    target = Path(tempfile.mkdtemp(prefix="lcgkit-scan-"))
    for name in done.stdout.splitlines():
        source = root / name
        if source.is_file():
            (target / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target / name)
    return target


def _run(name: str, command: list[str], cwd: Path) -> dict[str, Any]:
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as error:
        return {"name": name, "status": "FAIL", "output_tail": f"cannot run {command[0]}: {error}"}
    tail = "\n".join((done.stdout + done.stderr).splitlines()[-TAIL_LINES:])
    return {"name": name, "status": "PASS" if done.returncode == 0 else "FAIL", "output_tail": tail}


def _secrets(root: Path) -> dict[str, Any]:
    if shutil.which("gitleaks") is None:
        return {"name": "secrets", "status": "FAIL", "output_tail": MISSING_GITLEAKS}
    if (root / ".env").exists() and not env_is_ignored(root):
        return {"name": "secrets", "status": "FAIL", "output_tail": ".env exists and is not ignored by Git"}
    base = ["gitleaks", "--config", str(CONFIG), "--no-banner", "--redact"]
    history = _run("secrets", [base[0], "git", *base[1:], str(_git_root(root))], root)
    copy = tracked_copy(root)
    try:
        files = _run("secrets", [base[0], "dir", *base[1:], str(copy)], root)
    finally:
        shutil.rmtree(copy, ignore_errors=True)
    failed = [part for part in (history, files) if part["status"] == "FAIL"]
    return failed[0] if failed else {"name": "secrets", "status": "PASS", "output_tail": ""}


def _integrity(root: Path) -> dict[str, Any]:
    problems = integrity.check(root)
    detail = "\n".join(f"{p['rule']}: {p['detail']}" for p in problems)
    return {"name": "integrity", "status": "FAIL" if problems else "PASS", "output_tail": detail}


def run_prechecks(root: Path) -> list[dict[str, Any]]:
    """Run lint, security, tests, secrets and integrity, in that order, and report each.

    Task: T013. Covers: FR-030, AC-058, SC-009.
    """
    return [
        _run("lint", [_tool("ruff"), "check", "src", "tests", "--no-cache"], root),
        _run("security", [_tool("bandit"), "-r", "src", "-ll", "-q"], root),
        _run("tests", [_tool("pytest"), "tests", "-q", "-p", "no:cacheprovider"], root),
        _secrets(root),
        _integrity(root),
    ]
