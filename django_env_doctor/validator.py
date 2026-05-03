"""
Validation logic for environment variables against their schema.
"""

import os
from typing import Any, Dict, List, Optional

from .caster import cast_value
from .exceptions import EnvCastError, EnvSchemaError
from .types import EnvVarResult, EnvVarSchema, EnvVarType, IssueLevel


def validate_all(
    schema: Dict[str, EnvVarSchema],
    environ: Optional[Dict[str, str]] = None,
    current_environment: Optional[str] = None,
) -> List[EnvVarResult]:
    """
    Validate all env variables in the schema against the environment.

    Returns a list of EnvVarResult, one per variable.
    """
    if environ is None:
        environ = dict(os.environ)

    results = []
    for name, var_schema in schema.items():
        result = validate_one(name, var_schema, environ, current_environment)
        results.append(result)

    return results


def validate_one(
    name: str,
    var_schema: EnvVarSchema,
    environ: Dict[str, str],
    current_environment: Optional[str] = None,
) -> EnvVarResult:
    """Validate a single environment variable."""

    # Check if this variable applies to the current environment
    if var_schema.environments and current_environment:
        if current_environment not in var_schema.environments:
            return EnvVarResult(
                name=name,
                level=IssueLevel.SKIP,
                message=f"Not required in '{current_environment}' environment",
                schema=var_schema,
            )

    raw_value = environ.get(name)

    # Handle missing variable
    if raw_value is None:
        if var_schema.default is not None:
            return EnvVarResult(
                name=name,
                level=IssueLevel.OK,
                value=var_schema.default,
                raw_value=None,
                message="Using default value",
                schema=var_schema,
            )
        if not var_schema.required:
            return EnvVarResult(
                name=name,
                level=IssueLevel.SKIP,
                message="Optional, not set",
                schema=var_schema,
            )
        return EnvVarResult(
            name=name,
            level=IssueLevel.MISSING,
            message="Required variable is not set",
            schema=var_schema,
        )

    # Cast the value
    try:
        value = cast_value(raw_value, var_schema.type, name)
    except EnvCastError as e:
        return EnvVarResult(
            name=name,
            level=IssueLevel.INVALID,
            raw_value=raw_value,
            message=e.message,
            schema=var_schema,
        )

    # Run additional validation rules
    issue = _run_rules(name, value, raw_value, var_schema)
    if issue:
        return issue

    return EnvVarResult(
        name=name,
        level=IssueLevel.OK,
        value=value,
        raw_value=raw_value,
        message="",
        schema=var_schema,
    )


def _run_rules(
    name: str,
    value: Any,
    raw_value: str,
    schema: EnvVarSchema,
) -> Optional[EnvVarResult]:
    """Run additional validation rules. Returns an issue result or None if all pass."""

    # min_length
    if schema.min_length is not None:
        if not hasattr(value, "__len__") or len(value) < schema.min_length:
            return EnvVarResult(
                name=name,
                level=IssueLevel.INVALID,
                raw_value=raw_value,
                message=f"Value must be at least {schema.min_length} characters long",
                schema=schema,
            )

    # max_length
    if schema.max_length is not None:
        if not hasattr(value, "__len__") or len(value) > schema.max_length:
            return EnvVarResult(
                name=name,
                level=IssueLevel.INVALID,
                raw_value=raw_value,
                message=f"Value must be at most {schema.max_length} characters long",
                schema=schema,
            )

    # min (numeric)
    if schema.min is not None:
        try:
            if float(value) < schema.min:
                return EnvVarResult(
                    name=name,
                    level=IssueLevel.INVALID,
                    raw_value=raw_value,
                    message=f"Value must be >= {schema.min}",
                    schema=schema,
                )
        except (TypeError, ValueError):
            pass

    # max (numeric)
    if schema.max is not None:
        try:
            if float(value) > schema.max:
                return EnvVarResult(
                    name=name,
                    level=IssueLevel.INVALID,
                    raw_value=raw_value,
                    message=f"Value must be <= {schema.max}",
                    schema=schema,
                )
        except (TypeError, ValueError):
            pass

    # choices
    if schema.choices is not None:
        if value not in schema.choices:
            choices_str = ", ".join(str(c) for c in schema.choices)
            return EnvVarResult(
                name=name,
                level=IssueLevel.INVALID,
                raw_value=raw_value,
                message=f"Value '{value}' is not one of the allowed choices: [{choices_str}]",
                schema=schema,
            )

    return None
