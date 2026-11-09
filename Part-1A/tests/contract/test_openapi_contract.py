"""Contract tests: the service behaves as its OpenAPI description says (US9)."""

from pathlib import Path

import pytest
import schemathesis
import yaml
from lcgkit.service import app
from schemathesis import checks as common_checks
from schemathesis.specs.openapi import checks as openapi_checks

pytestmark = [pytest.mark.ac("AC-072"), pytest.mark.fr("FR-037")]

CONTRACT = Path(__file__).resolve().parents[2] / "specs/001-lcgkit-toolkit/contracts/openapi.yaml"
METHODS = {"get", "post"}
CHECKS = [
    common_checks.not_a_server_error,
    openapi_checks.status_code_conformance,
    openapi_checks.content_type_conformance,
    openapi_checks.response_schema_conformance,
]

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@schema.parametrize()
def test_generated_cases_match_the_description(case: schemathesis.Case) -> None:
    case.call_and_validate(checks=CHECKS)


def resolve(document: dict, node: dict) -> dict:
    """Follow local $ref pointers until a real object is reached."""
    while "$ref" in node:
        target = document
        for part in node["$ref"].lstrip("#/").split("/"):
            target = target[part]
        node = target
    return node


def property_names(document: dict, node: dict) -> set[str]:
    """Names of all properties a schema allows, looking through allOf, oneOf and anyOf."""
    node = resolve(document, node)
    names = set(node.get("properties", {}))
    for key in ("allOf", "oneOf", "anyOf"):
        for part in node.get(key, []):
            names |= property_names(document, part)
    return names


def shape(document: dict) -> dict[tuple[str, str], tuple[set[str], set[str]]]:
    """Map (path, method) to the request property names and the response statuses."""
    found = {}
    for path, methods in document["paths"].items():
        for method, operation in methods.items():
            if method not in METHODS:
                continue
            body = resolve(document, operation.get("requestBody", {}))
            content = body.get("content", {}).get("application/json", {}).get("schema", {})
            names = property_names(document, content) if content else set()
            found[(path, method)] = (names, set(operation["responses"]))
    return found


def test_the_generated_description_has_the_published_shape() -> None:
    published = yaml.safe_load(CONTRACT.read_text())
    assert shape(app.openapi()) == shape(published)
