"""The command line: a thin argparse adapter over the operations layer."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from lcgkit import ops, wire
from lcgkit.errors import LcgError
from lcgkit.fields import FIELDS, LARGE_LIST, OPERATIONS, SIGNED_LARGE, TEXT

EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_INVALID_INPUT = 2
EXIT_REFUSED = 3
REFUSED_CODE = "insecure-purpose"
STDIN_MARKER = "-"
INDENT = "  "
COUNTS = frozenset(name for name, f in FIELDS.items() if f.kind == "count")


def _parser() -> argparse.ArgumentParser:
    """One subcommand per registered operation; options are the field names with hyphens."""
    parser = argparse.ArgumentParser(prog="lcgkit", allow_abbrev=False)
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ops.HANDLERS:
        command = commands.add_parser(name, allow_abbrev=False)
        for field in sorted(OPERATIONS[name].allowed):
            command.add_argument(f"--{field.replace('_', '-')}", dest=field, default=None)
        command.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _outputs(text: str, field: str) -> list[int] | wire.InvalidField:
    """Read --outputs: comma-separated integers, or '-' for one per line on standard input."""
    pieces = sys.stdin.read().split() if text == STDIN_MARKER else text.split(",")
    items = [wire.decode_large(piece.strip(), field) for piece in pieces]
    numbers = [item for item in items if isinstance(item, int)]
    return numbers if len(numbers) == len(items) else wire.InvalidField(field, "invalid-type")


def _value(field: str, text: str) -> object:
    """Read one option's text: integers are plain decimal text, never rounded."""
    kind = FIELDS[field].kind
    if kind == TEXT:
        return text
    if kind == LARGE_LIST:
        return _outputs(text, field)
    return wire.decode_large(text, field, signed=kind == SIGNED_LARGE or field in COUNTS)



def _scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _lines(label: str, value: Any, depth: int) -> list[str]:
    """Render one result entry as indented readable text."""
    pad = INDENT * depth
    if isinstance(value, dict):
        nested = [line for k, v in value.items() for line in _lines(str(k), v, depth + 1)]
        return [f"{pad}{label}:", *nested]
    if isinstance(value, list) and any(isinstance(v, dict | list) for v in value):
        nested = [line for i, v in enumerate(value) for line in _lines(f"[{i}]", v, depth + 1)]
        return [f"{pad}{label}:", *nested]
    if isinstance(value, list):
        return [f"{pad}{label}: " + ", ".join(_scalar(v) for v in value)]
    return [f"{pad}{label}: {_scalar(value)}"]


def _render(operation: str, result: dict[str, Any], as_json: bool) -> str:
    if as_json:
        return json.dumps(wire.encode_result(operation, result), sort_keys=True)
    return "\n".join(line for key, value in result.items() for line in _lines(key, value, 0))


def _report(error: LcgError) -> int:
    where = f" (field: {error.field})" if error.field else ""
    print(f"error {error.code}: {error.message}{where}", file=sys.stderr)
    return EXIT_REFUSED if error.code == REFUSED_CODE else EXIT_INVALID_INPUT


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line; return the exit status.

    Task: T076. Covers: FR-032, FR-033, FR-034.
    """
    args = _parser().parse_args(argv)
    given = {
        name: _value(name, text)
        for name in OPERATIONS[args.operation].allowed
        if (text := getattr(args, name)) is not None
    }
    try:
        result = ops.run(args.operation, given)
        output = _render(args.operation, result, args.as_json)
    except LcgError as error:
        return _report(error)
    except Exception as exc:
        print(f"error: unexpected failure ({type(exc).__name__})", file=sys.stderr)
        return EXIT_UNEXPECTED
    print(output)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
