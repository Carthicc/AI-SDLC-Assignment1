"""The OpenAPI document of the service, built from the field table and the result schemas."""

from __future__ import annotations

from typing import Any

from lcgkit.fields import (
    FIELDS,
    LARGE,
    LARGE_LIST,
    MAX_COUNT,
    OPERATIONS,
    SIGNED_LARGE,
    TEXT,
    Operation,
)

# Result and shared schemas, as published in specs/001-lcgkit-toolkit/contracts/openapi.yaml.
SCHEMAS: dict[str, Any] = {
    "DecimalString": {
        "type": "string",
        "pattern": "^(0|[1-9][0-9]*)$",
        "description": (
            "A non-negative integer written as digits; "
            "used for every value that can exceed 2^53"
        )
    },
    "SignedDecimalString": {
        "type": "string",
        "pattern": "^(0|-?[1-9][0-9]*)$"
    },
    "Count": {
        "type": "integer",
        "minimum": 0,
        "maximum": 1000000
    },
    "Warnings": {
        "type": "array",
        "items": {
            "enum": [
                "zero-fixed-point",
                "degenerate-multiplier"
            ]
        }
    },
    "Secure": {
        "type": "boolean",
        "const": False,
        "description": "Always False; an LCG is not cryptographically secure"
    },
    "ErrorBody": {
        "type": "object",
        "required": [
            "error"
        ],
        "properties": {
            "error": {
                "type": "object",
                "required": [
                    "code",
                    "message"
                ],
                "properties": {
                    "code": {
                        "enum": [
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
                            "malformed-request"
                        ]
                    },
                    "message": {
                        "type": "string"
                    },
                    "field": {
                        "type": "string"
                    }
                }
            }
        }
    },
    "PresetList": {
        "type": "object",
        "required": [
            "presets",
            "cryptographically_secure"
        ],
        "properties": {
            "presets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "name",
                        "a",
                        "c",
                        "m",
                        "description"
                    ],
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "a": {
                            "$ref": "#/components/schemas/DecimalString"
                        },
                        "c": {
                            "$ref": "#/components/schemas/DecimalString"
                        },
                        "m": {
                            "$ref": "#/components/schemas/DecimalString"
                        },
                        "description": {
                            "type": "string"
                        }
                    }
                }
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    },
    "SequenceResult": {
        "type": "object",
        "required": [
            "outputs",
            "outputs_consumed",
            "next_state",
            "warnings",
            "cryptographically_secure"
        ],
        "properties": {
            "outputs": {
                "type": "array",
                "items": {
                    "$ref": "#/components/schemas/DecimalString"
                }
            },
            "outputs_consumed": {
                "type": "integer"
            },
            "next_state": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "warnings": {
                "$ref": "#/components/schemas/Warnings"
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    },
    "IntegersResult": {
        "type": "object",
        "required": [
            "values",
            "outputs_consumed",
            "next_state",
            "warnings",
            "cryptographically_secure"
        ],
        "properties": {
            "values": {
                "type": "array",
                "items": {
                    "$ref": "#/components/schemas/SignedDecimalString"
                }
            },
            "outputs_consumed": {
                "type": "integer"
            },
            "next_state": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "warnings": {
                "$ref": "#/components/schemas/Warnings"
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    },
    "FractionsResult": {
        "type": "object",
        "required": [
            "values",
            "outputs_consumed",
            "next_state",
            "warnings",
            "cryptographically_secure"
        ],
        "properties": {
            "values": {
                "type": "array",
                "items": {
                    "type": "number",
                    "minimum": 0,
                    "exclusiveMaximum": 1
                }
            },
            "outputs_consumed": {
                "type": "integer"
            },
            "next_state": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "warnings": {
                "$ref": "#/components/schemas/Warnings"
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    },
    "JumpResult": {
        "type": "object",
        "required": [
            "state",
            "warnings",
            "cryptographically_secure"
        ],
        "properties": {
            "state": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "warnings": {
                "$ref": "#/components/schemas/Warnings"
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    },
    "StreamsResult": {
        "type": "object",
        "required": [
            "streams",
            "warnings",
            "cryptographically_secure"
        ],
        "properties": {
            "streams": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "index",
                        "start_state",
                        "outputs"
                    ],
                    "properties": {
                        "index": {
                            "type": "integer"
                        },
                        "start_state": {
                            "$ref": "#/components/schemas/DecimalString"
                        },
                        "outputs": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/DecimalString"
                            }
                        }
                    }
                }
            },
            "warnings": {
                "$ref": "#/components/schemas/Warnings"
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    },
    "Condition": {
        "type": "object",
        "required": [
            "name",
            "passed"
        ],
        "properties": {
            "name": {
                "enum": [
                    "increment-not-coprime",
                    "multiplier-minus-one-not-divisible-by-prime-factor",
                    "multiplier-minus-one-not-divisible-by-four"
                ]
            },
            "passed": {
                "type": "boolean"
            }
        }
    },
    "Verdict": {
        "type": "object",
        "required": [
            "verdict",
            "conditions",
            "reasons",
            "cryptographically_secure"
        ],
        "properties": {
            "verdict": {
                "enum": [
                    "full-period",
                    "not-full-period"
                ]
            },
            "expected_period": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "conditions": {
                "type": "array",
                "items": {
                    "$ref": "#/components/schemas/Condition"
                }
            },
            "reasons": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    },
    "QualityReport": {
        "type": "object",
        "required": [
            "measured_period",
            "chi_square",
            "p_value",
            "serial_correlation",
            "low_bit_periods",
            "checks",
            "verdict",
            "notice",
            "cryptographically_secure"
        ],
        "properties": {
            "measured_period": {
                "oneOf": [
                    {
                        "$ref": "#/components/schemas/DecimalString"
                    },
                    {
                        "const": "not-computed"
                    }
                ]
            },
            "chi_square": {
                "type": "number"
            },
            "p_value": {
                "type": "number"
            },
            "serial_correlation": {
                "oneOf": [
                    {
                        "type": "number"
                    },
                    {
                        "const": "undefined"
                    }
                ]
            },
            "low_bit_periods": {
                "oneOf": [
                    {
                        "type": "object",
                        "required": [
                            "1",
                            "2",
                            "3"
                        ],
                        "properties": {
                            "1": {
                                "type": "integer"
                            },
                            "2": {
                                "type": "integer"
                            },
                            "3": {
                                "type": "integer"
                            }
                        }
                    },
                    {
                        "const": "not-applicable"
                    }
                ]
            },
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "name",
                        "outcome"
                    ],
                    "properties": {
                        "name": {
                            "enum": [
                                "period-covers-sample",
                                "uniformity",
                                "independence",
                                "low-bits"
                            ]
                        },
                        "value": {},
                        "outcome": {
                            "enum": [
                                "pass",
                                "fail",
                                "not-applicable"
                            ]
                        }
                    }
                }
            },
            "verdict": {
                "enum": [
                    "defect-detected",
                    "caution",
                    "no-defect-detected"
                ]
            },
            "notice": {
                "type": "string"
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    },
    "Prediction": {
        "type": "object",
        "required": [
            "case",
            "predictions",
            "notice",
            "cryptographically_secure"
        ],
        "properties": {
            "case": {
                "enum": [
                    "A",
                    "B",
                    "C"
                ]
            },
            "modulus": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "a": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "c": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "state": {
                "$ref": "#/components/schemas/DecimalString"
            },
            "predictions": {
                "type": "array",
                "items": {
                    "$ref": "#/components/schemas/DecimalString"
                }
            },
            "notice": {
                "type": "string"
            },
            "cryptographically_secure": {
                "$ref": "#/components/schemas/Secure"
            }
        }
    }
}

RESULT_SCHEMA = {
    "presets": "PresetList",
    "sequence": "SequenceResult",
    "integers": "IntegersResult",
    "fractions": "FractionsResult",
    "jump": "JumpResult",
    "streams": "StreamsResult",
    "validate": "Verdict",
    "quality": "QualityReport",
    "predict": "Prediction",
}
SUMMARY = {
    "presets": "List the named generators",
    "sequence": "Generate a sequence",
    "integers": "Draw fair integers from an inclusive range",
    "fractions": "Draw fractions in [0, 1)",
    "jump": "State after a number of steps",
    "streams": "Split a sequence into separate streams",
    "validate": "Check whether parameters reach a full period",
    "quality": "Quality report for a generator's output",
    "predict": "Predict what comes next from observed outputs",
}


def _ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/components/schemas/{name}"}


def _property(name: str) -> dict[str, Any]:
    """The schema of one request field, from its kind in the field table."""
    kind = FIELDS[name].kind
    if kind == LARGE:
        return _ref("DecimalString")
    if kind == SIGNED_LARGE:
        return _ref("SignedDecimalString")
    if kind == TEXT:
        return {"type": "string"}
    if kind == LARGE_LIST:
        return {"type": "array", "maxItems": MAX_COUNT, "items": _ref("DecimalString")}
    if name == "hidden_bits":
        return {"type": "integer", "minimum": 0}
    return _ref("Count")


def _request_body(spec: Operation) -> dict[str, Any]:
    """A request body listing exactly the fields the operation accepts."""
    names = sorted(spec.allowed, key=_field_rank)
    schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {name: _property(name) for name in names},
    }
    required = [n for n in spec.order if n not in spec.optional]
    if required:
        schema["required"] = required
    return {"required": True, "content": {"application/json": {"schema": schema}}}


def _field_rank(name: str) -> int:
    return list(FIELDS).index(name)


def _responses(spec: Operation) -> dict[str, Any]:
    success = {
        "description": "The result",
        "content": {"application/json": {"schema": _ref(RESULT_SCHEMA[spec.name])}},
    }
    error = {
        "description": "One error, the first in the fixed checking order",
        "content": {"application/json": {"schema": _ref("ErrorBody")}},
    }
    responses: dict[str, Any] = {"200": success}
    if spec.name != "presets":
        responses["400"] = error
    if spec.purpose:
        responses["403"] = {**error, "description": "The declared purpose is refused"}
    return responses


def _operation(spec: Operation) -> dict[str, Any]:
    entry: dict[str, Any] = {"operationId": spec.name, "summary": SUMMARY[spec.name]}
    if spec.name != "presets":
        entry["requestBody"] = _request_body(spec)
    entry["responses"] = _responses(spec)
    return entry


def build_document() -> dict[str, Any]:
    """Build the OpenAPI 3.1 document from the field table.

    Task: T078. Covers: FR-037.
    """
    paths = {
        f"/v1/{name}": {("get" if name == "presets" else "post"): _operation(spec)}
        for name, spec in OPERATIONS.items()
    }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "lcgkit",
            "version": "1.0.0",
            "description": (
                "Stateless linear congruential generator service. Nothing is stored between "
                "requests. Integers that can exceed 2^53 travel as decimal strings. A request "
                "with several mistakes gets one error, chosen in a fixed field order. Output "
                "of this service is not cryptographically secure."
            ),
        },
        "paths": paths,
        "components": {"schemas": SCHEMAS},
    }
