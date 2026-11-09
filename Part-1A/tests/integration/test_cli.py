"""Tests for the command line (US8), run as `python -m lcgkit.cli` in a subprocess.

The comparison with the library is a relative check: the JSON printed by the command line must
equal the library's result for the same input. The absolute values are covered by the
per-operation tests.
"""

import contextlib
import io
import json
import subprocess
import sys

import pytest
from lcgkit.cli import main
from lcgkit.ops import run

from lcgkit import wire
from tests.helpers import EXAMPLES, cli_args, leaves

pytestmark = [
    pytest.mark.fr("FR-005"),
    pytest.mark.fr("FR-032"),
    pytest.mark.fr("FR-033"),
    pytest.mark.fr("FR-034"),
]

EXIT_INVALID_INPUT = 2
EXIT_REFUSED = 3
IDS = [f"{operation}-{index}" for index, (operation, _) in enumerate(EXAMPLES)]


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the command line and capture everything it prints."""
    return subprocess.run(
        [sys.executable, "-m", "lcgkit.cli", *args],
        capture_output=True, text=True, encoding="utf-8", check=False, timeout=120,
    )


@pytest.mark.ac("AC-061")
@pytest.mark.ac("AC-062")
@pytest.mark.parametrize(("operation", "request_body"), EXAMPLES, ids=IDS)
def test_json_output_equals_the_library_result(
    operation: str, request_body: dict[str, object]
) -> None:
    done = cli(operation, *cli_args(request_body), "--json")
    assert done.returncode == 0, done.stderr
    assert done.stderr == ""
    expected = wire.encode_result(operation, run(operation, request_body))
    assert json.loads(done.stdout) == expected


@pytest.mark.ac("AC-063")
def test_large_integers_are_strings_and_counts_are_numbers() -> None:
    args = cli_args({"preset": "pcg-lcg64", "seed": 0, "count": 3})
    data = json.loads(cli("sequence", *args, "--json").stdout)
    assert all(isinstance(value, str) for value in data["outputs"])
    assert isinstance(data["next_state"], str)
    assert isinstance(data["outputs_consumed"], int)
    streams = json.loads(
        cli("streams", *cli_args({"preset": "glibc-type0", "seed": 1, "streams": 2, "length": 3}),
            "--json").stdout
    )["streams"]
    assert isinstance(streams[0]["index"], int)
    assert isinstance(streams[0]["start_state"], str)


@pytest.mark.ac("AC-064")
@pytest.mark.parametrize(("operation", "request_body"), EXAMPLES, ids=IDS)
def test_text_output_contains_the_same_values(
    operation: str, request_body: dict[str, object]
) -> None:
    done = cli(operation, *cli_args(request_body))
    assert done.returncode == 0, done.stderr
    with pytest.raises(ValueError):
        json.loads(done.stdout)
    for leaf in leaves(run(operation, request_body)):
        assert str(leaf) in done.stdout


@pytest.mark.ac("AC-065")
def test_invalid_input_exits_with_2_and_prints_only_to_standard_error() -> None:
    done = cli("sequence", "--a=5", "--c=3", "--m=16", "--seed=16", "--count=5")
    assert done.returncode == EXIT_INVALID_INPUT
    assert done.stdout == ""
    assert done.stderr.startswith("error invalid-seed:")


@pytest.mark.ac("AC-065")
def test_a_number_that_is_not_decimal_text_is_an_input_error() -> None:
    done = cli("sequence", "--a=5", "--c=3", "--m=16", "--seed=0x10", "--count=5")
    assert done.returncode == EXIT_INVALID_INPUT
    assert done.stdout == ""
    assert done.stderr.startswith("error invalid-type:")


@pytest.mark.ac("AC-065")
def test_a_refused_purpose_exits_with_3() -> None:
    done = cli("sequence", "--preset=minstd", "--seed=1", "--count=3", "--purpose=token")
    assert done.returncode == EXIT_REFUSED
    assert done.stdout == ""
    assert done.stderr.startswith("error insecure-purpose:")


@pytest.mark.ac("AC-065")
def test_bad_usage_exits_with_2() -> None:
    done = cli("no-such-command")
    assert done.returncode == EXIT_INVALID_INPUT
    assert done.stdout == ""


def test_one_hundred_runs_in_process_print_the_same_text() -> None:
    argv = ["sequence", "--a=5", "--c=3", "--m=16", "--seed=7", "--count=5", "--json"]
    outputs = set()
    for _ in range(100):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            assert main(argv) == 0
        outputs.add(buffer.getvalue())
    assert len(outputs) == 1
