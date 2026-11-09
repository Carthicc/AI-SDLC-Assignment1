"""The library, the command line and the HTTP service give the same answer (US9).

This is a relative check: the three results are compared with each other on a shared set of
examples. The absolute values are covered by the per-operation tests.
"""

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from lcgkit import wire
from lcgkit.ops import run
from lcgkit.service import app
from tests.helpers import EXAMPLES, cli_args, http_body

pytestmark = [pytest.mark.ac("AC-073"), pytest.mark.fr("FR-038")]

client = TestClient(app)
IDS = [f"{operation}-{index}" for index, (operation, _) in enumerate(EXAMPLES)]


@pytest.mark.parametrize(("operation", "request_body"), EXAMPLES, ids=IDS)
def test_library_cli_and_service_agree(operation: str, request_body: dict[str, object]) -> None:
    library = wire.encode_result(operation, run(operation, request_body))
    done = subprocess.run(
        [sys.executable, "-m", "lcgkit.cli", operation, *cli_args(request_body), "--json"],
        capture_output=True, text=True, encoding="utf-8", check=False, timeout=120,
    )
    assert done.returncode == 0, done.stderr
    if operation == "presets":
        response = client.get("/v1/presets")
    else:
        response = client.post(f"/v1/{operation}", json=http_body(request_body))
    assert response.status_code == 200
    assert json.loads(done.stdout) == library
    assert response.json() == library
