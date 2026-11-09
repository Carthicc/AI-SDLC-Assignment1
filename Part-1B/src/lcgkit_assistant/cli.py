"""The command line: `lcgkit-assistant "request text"` or `lcgkit-assistant --info`."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from typing import Any

from lcgkit_assistant import config
from lcgkit_assistant.assistant import Client, handle


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lcgkit-assistant", description="Run an lcgkit request written in plain language."
    )
    parser.add_argument("text", nargs="?", help="the request text")
    parser.add_argument(
        "--info", action="store_true", help="print the model, settings and prompt hash"
    )
    return parser


def _info() -> dict[str, Any]:
    settings = {"temperature": config.TEMPERATURE, "response_format": config.RESPONSE_FORMAT}
    return {"model": config.MODEL, "settings": settings, "prompt_sha256": config.prompt_sha256()}


def _exit_status(answer: dict[str, Any]) -> int:
    error = answer.get("error")
    code = error.get("code") if isinstance(error, dict) else None
    return config.EXIT_APPLICATION_ERROR if code in config.ERROR_CODES else config.EXIT_OK


def main(
    argv: list[str] | None = None,
    client: Client | None = None,
    environ: Mapping[str, str] | None = None,
) -> int:
    """Print the answer for one request text (or the info) and return the exit status.

    Task: T045. Covers: FR-013, FR-015, AC-056, AC-061.
    """
    parser = _parser()
    args = parser.parse_args(argv)
    if args.info:
        print(json.dumps(_info(), sort_keys=True))
        return config.EXIT_OK
    if args.text is None:
        parser.error("a request text or --info is required")
    answer = handle(args.text, client=client, environ=environ)
    print(json.dumps(answer, sort_keys=True))
    return _exit_status(answer)


if __name__ == "__main__":
    sys.exit(main())
