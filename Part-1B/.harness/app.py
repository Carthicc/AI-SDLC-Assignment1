"""Runs the application's command line as a subprocess (task T010).

This module never imports the application: it only starts it and reads what it prints.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


def default_command() -> list[str]:
    """The command that starts the application."""
    return [sys.executable, "-m", "lcgkit_assistant.cli"]


def _failure(message: str) -> dict[str, Any]:
    return {"reply": None, "error": {"code": "harness-app-failure", "message": message}, "model_calls": 0}


def _json_object(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def run_app(text: str, command: list[str], timeout: int, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Run the application on one request text and return its answer.

    If the process cannot start, times out or prints something that is not a JSON object, the
    result is a failure answer, so that the case fails instead of the run crashing.

    Task: T010. Covers: FR-013, FR-025, AC-047.
    """
    try:
        done = subprocess.run(
            [*command, text], capture_output=True, text=True, timeout=timeout, env=env, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return _failure(f"the application could not be run: {type(error).__name__}")
    answer = _json_object(done.stdout.strip())
    if answer is None:
        return _failure(f"the application printed no JSON object (exit status {done.returncode})")
    return answer


def app_info(command: list[str], timeout: int = 60, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Read the model, settings and prompt hash with `--info`.

    Task: T010. Covers: AC-061.
    """
    done = subprocess.run(
        [*command, "--info"], capture_output=True, text=True, timeout=timeout, env=env, check=False
    )
    info = _json_object(done.stdout.strip())
    if info is None:
        raise RuntimeError("the application's --info did not print a JSON object")
    return info
