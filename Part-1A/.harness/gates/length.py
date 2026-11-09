"""Length gate: no function or method may be longer than 40 lines (Ruff has no such rule)."""

from __future__ import annotations

import ast

from common import GateResult, GateRun, failure, gate_main, python_files, repo_root

MAX_LINES = 40


def run(gate: GateRun) -> GateResult:
    """List every function under src/ longer than MAX_LINES."""
    root = repo_root()
    failures = []
    for path in python_files(root / "src"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                gate.note(f"{path.relative_to(root)}:{node.lineno} {node.name} {length} lines")
                if length > MAX_LINES:
                    where = f"{path.relative_to(root)}:{node.lineno} {node.name}"
                    failures.append(
                        failure("function-length", f"at most {MAX_LINES} lines",
                                f"{where} has {length} lines", [])
                    )
    return gate.finish(failures)


if __name__ == "__main__":
    gate_main("length", run)
