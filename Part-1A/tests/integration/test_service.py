"""Tests for the HTTP service (US9), with FastAPI's in-process test client."""

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from lcgkit.errors import ERROR_CODES
from lcgkit.service import app

from tests.helpers import EXAMPLES, http_body

pytestmark = [
    pytest.mark.fr("FR-001"),
    pytest.mark.fr("FR-005"),
    pytest.mark.fr("FR-035"),
    pytest.mark.fr("FR-036"),
]

client = TestClient(app)
WORKED = {"a": "5", "c": "3", "m": "16", "seed": "7", "count": 5}
JSON_HEADER = {"content-type": "application/json"}
IDS = [f"{operation}-{index}" for index, (operation, _) in enumerate(EXAMPLES)]
BAD_LARGE = [5, "0x10", "1e3", "007", " 5"]  # a JSON number, then strings that are not decimal
LARGE_FIELD_CASES = [
    ("sequence", WORKED, "m"),
    ("sequence", WORKED, "a"),
    ("sequence", WORKED, "c"),
    ("sequence", WORKED, "seed"),
    ("jump", {"preset": "minstd", "state": "1", "steps": "10"}, "state"),
    ("jump", {"preset": "minstd", "state": "1", "steps": "10"}, "steps"),
    ("integers", {**WORKED, "lo": "1", "hi": "3"}, "lo"),
    ("integers", {**WORKED, "lo": "1", "hi": "3"}, "hi"),
]
BAD_REQUESTS = [
    (b"{not json", "malformed-request"),
    (b"", "malformed-request"),
    (b"[]", "malformed-request"),
    (b"null", "malformed-request"),
    (b'"text"', "malformed-request"),
    (b'{"a": "5", "c": "3", "m": "16", "seed": "7", "count": 5, "extra": 1}', "malformed-request"),
    (b'{"a": "5", "c": "3", "m": "16", "seed": "7"}', None),
    (b'{"a": "5", "c": "3", "m": "16", "seed": "7", "count": ' + b"9" * 500 + b"}", None),
    (b'{"a": "5", "c": "3", "m": "16", "seed": "7", "count": "five"}', "invalid-type"),
]


def call(operation: str, body: dict[str, object]) -> Response:
    """Send one operation to the service."""
    if operation == "presets":
        return client.get("/v1/presets")
    return client.post(f"/v1/{operation}", json=body)


def error_of(response: Response) -> dict[str, object]:
    """The error part of a failed response."""
    return dict(response.json()["error"])


@pytest.mark.ac("AC-066")
@pytest.mark.parametrize(("operation", "request_body"), EXAMPLES, ids=IDS)
def test_every_operation_is_available(operation: str, request_body: dict[str, object]) -> None:
    response = call(operation, http_body(request_body))
    assert response.status_code == 200
    assert response.json()["cryptographically_secure"] is False


@pytest.mark.ac("AC-066")
def test_a_follow_up_from_the_next_state_matches_one_longer_request() -> None:
    first = client.post("/v1/sequence", json=WORKED).json()
    more = client.post("/v1/sequence", json={**WORKED, "seed": first["next_state"], "count": 3})
    whole = client.post("/v1/sequence", json={**WORKED, "count": 8}).json()
    assert first["outputs"] + more.json()["outputs"] == whole["outputs"]


@pytest.mark.ac("AC-067")
@pytest.mark.parametrize(("operation", "request_body"), EXAMPLES, ids=IDS)
def test_identical_requests_get_identical_bodies(
    operation: str, request_body: dict[str, object]
) -> None:
    body = http_body(request_body)
    assert call(operation, body).content == call(operation, body).content


@pytest.mark.ac("AC-068")
def test_large_values_travel_as_decimal_strings() -> None:
    body = {"preset": "pcg-lcg64", "seed": "0", "count": 2}
    outputs = client.post("/v1/sequence", json=body).json()["outputs"]
    assert outputs == ["1442695040888963407", "1876011003808476466"]
    explicit = {"a": "6364136223846793005", "c": "1442695040888963407", "m": "18446744073709551616",
                "seed": "0", "count": 2}
    assert client.post("/v1/sequence", json=explicit).json()["outputs"] == outputs


@pytest.mark.ac("AC-069")
@pytest.mark.parametrize(("operation", "body", "field"), LARGE_FIELD_CASES)
@pytest.mark.parametrize("bad", BAD_LARGE)
def test_a_large_field_that_is_not_a_decimal_string_is_refused(
    operation: str, body: dict[str, object], field: str, bad: object
) -> None:
    response = client.post(f"/v1/{operation}", json={**body, field: bad})
    assert response.status_code == 400
    error = error_of(response)
    assert (error["code"], error["field"]) == ("invalid-type", field)


@pytest.mark.ac("AC-070")
def test_invalid_input_is_a_400_with_the_error_body() -> None:
    response = client.post("/v1/sequence", json={**WORKED, "seed": "16"})
    assert response.status_code == 400
    assert error_of(response)["code"] == "invalid-seed"
    assert set(error_of(response)) >= {"code", "message"}


@pytest.mark.ac("AC-070")
def test_a_refused_purpose_is_a_403() -> None:
    response = client.post("/v1/sequence", json={**WORKED, "purpose": "token"})
    assert response.status_code == 403
    assert error_of(response)["code"] == "insecure-purpose"


@pytest.mark.ac("AC-071")
@pytest.mark.parametrize(("content", "code"), BAD_REQUESTS)
def test_bad_requests_get_a_structured_client_error(content: bytes, code: str | None) -> None:
    response = client.post("/v1/sequence", content=content, headers=JSON_HEADER)
    assert response.status_code == 400
    found = error_of(response)["code"]
    assert found in ERROR_CODES
    if code is not None:
        assert found == code


@pytest.mark.ac("AC-071")
def test_a_missing_body_is_a_client_error() -> None:
    response = client.post("/v1/sequence")
    assert response.status_code == 400
    assert error_of(response)["code"] == "malformed-request"


def test_unknown_routes_and_methods_are_client_errors() -> None:
    responses = [client.get("/v1/nothing"), client.get("/v1/sequence"), client.post("/v1/presets")]
    for response in responses:
        assert response.status_code == 400
        assert error_of(response)["code"] == "malformed-request"


@pytest.mark.ac("AC-090")
def test_the_first_field_in_the_checking_order_decides() -> None:
    body = {"m": "1", "a": "0", "c": "0", "seed": "0", "count": "x"}
    first = client.post("/v1/sequence", json=body)
    assert error_of(first)["code"] == "invalid-modulus"
    second = client.post("/v1/sequence", json={**body, "unknown": 1})
    assert error_of(second)["code"] == "malformed-request"
