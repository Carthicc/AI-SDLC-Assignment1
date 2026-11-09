"""The HTTP service: a thin FastAPI adapter over the operations layer."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lcgkit import ops, wire
from lcgkit.errors import LcgError
from lcgkit.openapi import build_document

LOGGER = logging.getLogger("lcgkit.service")
HOST = "127.0.0.1"
DEFAULT_PORT = 8000
STATUS_OK = 200
STATUS_CLIENT_ERROR = 400
STATUS_REFUSED = 403
STATUS_SERVER_ERROR = 500
REFUSED_CODE = "insecure-purpose"



class Service(FastAPI):
    """The FastAPI application, with an OpenAPI document built from the field table."""

    def openapi(self) -> dict[str, Any]:
        """Return the document built by `lcgkit.openapi` (task T078)."""
        return DOCUMENT


DOCUMENT = build_document()
app = Service(title="lcgkit", docs_url=None, redoc_url=None)


def _error_response(error: LcgError) -> JSONResponse:
    status = STATUS_REFUSED if error.code == REFUSED_CODE else STATUS_CLIENT_ERROR
    return JSONResponse(error.to_body(), status_code=status)


def _parse(body: bytes) -> Any:
    """Parse a request body as JSON; anything that is not valid JSON is malformed."""
    try:
        return json.loads(body)
    except (ValueError, RecursionError) as exc:
        raise LcgError("malformed-request", "the body is not valid JSON") from exc


def _respond(operation: str, body: bytes) -> JSONResponse:
    """Parse, decode, run and encode one POST request; errors become structured bodies."""
    try:
        request = wire.decode_request(operation, _parse(body))
        result = ops.run(operation, request)
    except LcgError as error:
        return _error_response(error)
    return JSONResponse(wire.encode_result(operation, result), status_code=STATUS_OK)


def _post_route(operation: str) -> Callable[[Request], Awaitable[Response]]:
    async def endpoint(request: Request) -> Response:
        return _respond(operation, await request.body())

    return endpoint


async def _presets(request: Request) -> Response:
    return _respond("presets", b"{}")


def _register() -> None:
    """Add one route per registered operation (task T077)."""
    for name in ops.HANDLERS:
        if name == "presets":
            app.add_api_route("/v1/presets", _presets, methods=["GET"], include_in_schema=False)
        else:
            app.add_api_route(f"/v1/{name}", _post_route(name), methods=["POST"],
                              include_in_schema=False)


@app.exception_handler(StarletteHTTPException)
async def _unknown_route(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Unknown routes and methods get the same structured client error."""
    return _error_response(LcgError("malformed-request", "unknown route or method"))


@app.exception_handler(Exception)
async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
    """Reaching this is a defect: report it generically and log it."""
    LOGGER.exception("unexpected failure on %s %s", request.method, request.url.path)
    body = {"error": {"code": "internal-error", "message": "unexpected failure"}}
    return JSONResponse(body, status_code=STATUS_SERVER_ERROR)


@app.middleware("http")
async def _log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """One log line per request: method, path and status, never the body (task T079)."""
    response = await call_next(request)
    LOGGER.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


_register()


def serve() -> None:
    """Start the service on 127.0.0.1 (option --port).

    Task: T079. Covers: FR-035.
    """
    parser = argparse.ArgumentParser(description="Run the lcgkit HTTP service.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    uvicorn.run(app, host=HOST, port=parser.parse_args().port)
