"""Small JSON Schema subset validator used without third-party dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    """Raised when structured automation state does not match its contract."""


def _fail(path: str, message: str) -> None:
    raise SchemaValidationError(f"{path}: {message}")


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise SchemaValidationError(f"Unsupported schema type: {expected!r}")


def validate_instance(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        _fail(path, f"expected constant {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        _fail(path, f"value {value!r} is not in the allowed enum")

    expected = schema.get("type")
    if expected is not None:
        allowed_types = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, item) for item in allowed_types):
            _fail(path, f"expected type {expected!r}, got {type(value).__name__}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                _fail(path, f"missing required property {key!r}")
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            if extras:
                _fail(path, f"unexpected properties: {', '.join(extras)}")
        for key, child in value.items():
            if key in properties:
                validate_instance(child, properties[key], f"{path}.{key}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            _fail(path, f"expected at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            _fail(path, f"expected at most {schema['maxItems']} items")
        item_schema = schema.get("items")
        if item_schema:
            for index, child in enumerate(value):
                validate_instance(child, item_schema, f"{path}[{index}]")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            _fail(path, f"expected at least {schema['minLength']} characters")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            _fail(path, f"expected at most {schema['maxLength']} characters")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            _fail(path, f"does not match pattern {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            _fail(path, f"must be at least {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            _fail(path, f"must be at most {schema['maximum']}")


def validate_json_file(instance_path: Path, schema_path: Path) -> Any:
    with instance_path.open("r", encoding="utf-8") as handle:
        instance = json.load(handle)
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    validate_instance(instance, schema)
    return instance
