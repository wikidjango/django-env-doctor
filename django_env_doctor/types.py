"""
Type definitions and constants for django-env-doctor.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class EnvVarType(str, Enum):
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    URL = "url"
    EMAIL = "email"
    JSON = "json"
    LIST = "list"
    PATH = "path"


class IssueLevel(str, Enum):
    OK = "OK"
    MISSING = "MISSING"
    INVALID = "INVALID"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class EnvVarSchema:
    """Schema definition for a single environment variable."""

    type: EnvVarType = EnvVarType.STR
    required: bool = True
    default: Any = None
    description: str = ""
    secret: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min: Optional[float] = None
    max: Optional[float] = None
    choices: Optional[List[Any]] = None
    environments: Optional[List[str]] = None  # e.g. ["production", "staging"]

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = EnvVarType(self.type)


@dataclass
class EnvVarResult:
    """Result of validating a single environment variable."""

    name: str
    level: IssueLevel
    value: Any = None
    raw_value: Optional[str] = None
    message: str = ""
    schema: Optional[EnvVarSchema] = None

    @property
    def is_ok(self) -> bool:
        return self.level in (IssueLevel.OK, IssueLevel.SKIP)

    @property
    def has_issue(self) -> bool:
        return self.level in (IssueLevel.MISSING, IssueLevel.INVALID, IssueLevel.WARN)
