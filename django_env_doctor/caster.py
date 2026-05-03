"""
Type casting logic for environment variable values.
"""

import json
import os
import re
from typing import Any
from urllib.parse import urlparse

from .exceptions import EnvCastError
from .types import EnvVarType


def cast_value(raw: str, var_type: EnvVarType, name: str) -> Any:
    """
    Cast a raw string environment variable to the target Python type.

    Raises EnvCastError if casting fails.
    """
    casters = {
        EnvVarType.STR: _cast_str,
        EnvVarType.INT: _cast_int,
        EnvVarType.FLOAT: _cast_float,
        EnvVarType.BOOL: _cast_bool,
        EnvVarType.URL: _cast_url,
        EnvVarType.EMAIL: _cast_email,
        EnvVarType.JSON: _cast_json,
        EnvVarType.LIST: _cast_list,
        EnvVarType.PATH: _cast_path,
    }

    caster = casters.get(var_type)
    if caster is None:
        raise EnvCastError(name, raw, var_type, f"Unknown type: {var_type}")

    try:
        return caster(raw, name)
    except EnvCastError:
        raise
    except Exception as e:
        raise EnvCastError(name, raw, var_type, str(e))


def _cast_str(raw: str, name: str) -> str:
    return raw


def _cast_int(raw: str, name: str) -> int:
    try:
        return int(raw)
    except ValueError:
        raise EnvCastError(name, raw, EnvVarType.INT, f"Cannot convert '{raw}' to int")


def _cast_float(raw: str, name: str) -> float:
    try:
        return float(raw)
    except ValueError:
        raise EnvCastError(name, raw, EnvVarType.FLOAT, f"Cannot convert '{raw}' to float")


def _cast_bool(raw: str, name: str) -> bool:
    true_values = {"true", "1", "yes", "on", "t"}
    false_values = {"false", "0", "no", "off", "f"}
    normalized = raw.strip().lower()
    if normalized in true_values:
        return True
    if normalized in false_values:
        return False
    raise EnvCastError(
        name,
        raw,
        EnvVarType.BOOL,
        f"Cannot convert '{raw}' to bool. Use: true/false, 1/0, yes/no, on/off",
    )


def _cast_url(raw: str, name: str) -> str:
    try:
        parsed = urlparse(raw)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Missing scheme or host")
        return raw
    except Exception:
        raise EnvCastError(
            name, raw, EnvVarType.URL, f"'{raw}' is not a valid URL (e.g. https://example.com)"
        )


def _cast_email(raw: str, name: str) -> str:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, raw.strip()):
        raise EnvCastError(name, raw, EnvVarType.EMAIL, f"'{raw}' is not a valid email address")
    return raw.strip()


def _cast_json(raw: str, name: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise EnvCastError(name, raw, EnvVarType.JSON, f"Invalid JSON: {e}")


def _cast_list(raw: str, name: str) -> list:
    """
    Supports comma-separated values: "a,b,c" -> ["a", "b", "c"]
    Also supports JSON arrays: '["a","b","c"]' -> ["a", "b", "c"]
    """
    stripped = raw.strip()
    if stripped.startswith("["):
        try:
            result = json.loads(stripped)
            if not isinstance(result, list):
                raise ValueError("Not a list")
            return result
        except (json.JSONDecodeError, ValueError):
            raise EnvCastError(name, raw, EnvVarType.LIST, f"'{raw}' is not a valid JSON array")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _cast_path(raw: str, name: str) -> str:
    return os.path.expandvars(os.path.expanduser(raw.strip()))
