"""Error codes and the one exception type that every interface reports."""

from __future__ import annotations

ERROR_CODES: tuple[str, ...] = (
    "invalid-modulus",
    "invalid-multiplier",
    "invalid-increment",
    "invalid-seed",
    "invalid-type",
    "invalid-count",
    "count-exceeds-limit",
    "invalid-jump",
    "invalid-range",
    "range-exceeds-modulus",
    "invalid-bins",
    "unknown-preset",
    "insecure-purpose",
    "insufficient-data",
    "ambiguous-parameters",
    "stream-exceeds-modulus",
    "unsupported-combination",
    "malformed-request",
)


class LcgError(Exception):
    """A problem with a request, with a stable code, a message and the field it concerns."""

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        """Create an error; a code outside ERROR_CODES is a programming mistake (ValueError).

        Task: T056. Covers: FR-001, FR-036.
        """
        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code: {code}")
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field

    def to_body(self) -> dict[str, dict[str, str]]:
        """Return the structured error body, leaving out `field` when there is none.

        Task: T056. Covers: FR-036.
        """
        body = {"code": self.code, "message": self.message}
        if self.field is not None:
            body["field"] = self.field
        return {"error": body}
