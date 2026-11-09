"""The self-check shows that every layer of the harness can fail."""

import subprocess
import sys
from pathlib import Path

import pytest

SELFCHECK = Path(__file__).parents[2] / ".harness" / "selfcheck.py"


@pytest.mark.ac("AC-044")
@pytest.mark.ac("AC-051")
@pytest.mark.fr("FR-022")
def test_each_broken_fake_is_caught_by_the_layer_built_to_catch_it():
    done = subprocess.run(
        [sys.executable, str(SELFCHECK)], capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stdout
    lines = {line.split()[0]: line for line in done.stdout.splitlines() if line.split()}
    assert "PASS" in lines["good"]
    for mode, seen in {
        "extra-field": "INV-02",
        "invented-seed": "PROP-01",
        "leaks-key": "PROP-06",
        "wrong-decision": "FAIL",
        "no-answer": "INV-01",
    }.items():
        assert seen in lines[mode], lines[mode]
        assert lines[mode].rstrip().endswith("yes")
    assert "SELFCHECK PASS" in done.stdout
