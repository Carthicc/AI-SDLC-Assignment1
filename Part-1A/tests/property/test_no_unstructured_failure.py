"""No input makes the library or the service fail in an unstructured way (SC-007)."""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st
from lcgkit.errors import ERROR_CODES, LcgError
from lcgkit.ops import run
from lcgkit.service import app

pytestmark = [pytest.mark.fr("FR-036")]

client = TestClient(app)
POST_OPERATIONS = ["sequence", "integers", "fractions", "jump", "streams", "validate",
                   "quality", "predict"]
FIELD_NAMES = ["preset", "m", "a", "c", "seed", "state", "count", "lo", "hi", "steps",
               "sample_size", "bins", "outputs", "hidden_bits", "k", "streams", "length",
               "purpose", "unknown"]
SERVER_ERROR = 500

scalars = st.one_of(
    st.none(), st.booleans(), st.integers(-50, 50), st.integers(), st.floats(),
    st.text(max_size=8),
)
json_values = st.recursive(
    scalars,
    lambda inner: st.one_of(
        st.lists(inner, max_size=4), st.dictionaries(st.text(max_size=5), inner, max_size=4)
    ),
    max_leaves=8,
)
field_dicts = st.dictionaries(st.sampled_from(FIELD_NAMES), json_values, max_size=8)
requests = st.one_of(json_values, field_dicts)


@given(st.sampled_from([*POST_OPERATIONS, "presets"]), requests)
def test_the_library_returns_a_result_or_a_structured_error(operation: str, body: Any) -> None:
    try:
        result = run(operation, body)
    except LcgError as error:
        assert error.code in ERROR_CODES
    else:
        assert isinstance(result, dict)


@given(st.sampled_from(POST_OPERATIONS), requests)
def test_the_service_never_answers_with_a_server_error(operation: str, body: object) -> None:
    response = client.post(
        f"/v1/{operation}",
        content=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    assert response.status_code < SERVER_ERROR
    if response.status_code != 200:
        assert response.json()["error"]["code"] in ERROR_CODES


@given(st.sampled_from(POST_OPERATIONS), st.binary(max_size=60))
def test_the_service_survives_arbitrary_bytes(operation: str, content: bytes) -> None:
    response = client.post(
        f"/v1/{operation}", content=content, headers={"content-type": "application/json"}
    )
    assert response.status_code < SERVER_ERROR
