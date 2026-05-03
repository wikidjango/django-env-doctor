"""
Main public API for django-env-doctor.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import EnvSchemaError, EnvValidationError
from .loader import generate_example_file, load_env_file
from .reporter import format_report
from .types import EnvVarResult, EnvVarSchema, EnvVarType, IssueLevel
from .validator import validate_all


class DjangoEnv:
    """
    The main interface for django-env-doctor.

    Handles loading, validation, and access of environment variables.

    Usage::

        from django_env_doctor import DjangoEnv

        env = DjangoEnv(
            schema={
                "SECRET_KEY": {"type": "str", "required": True, "secret": True, "min_length": 40},
                "DEBUG": {"type": "bool", "default": False},
                "DATABASE_URL": {"type": "url", "required": True},
                "ALLOWED_HOSTS": {"type": "list", "default": []},
            },
            load_file=True,
            env_file=".env",
            raise_on_error=True,
        )

        SECRET_KEY = env("SECRET_KEY")
        DEBUG = env("DEBUG")
    """

    def __init__(
        self,
        schema: Dict[str, Union[Dict, EnvVarSchema]],
        load_file: bool = True,
        env_file: Optional[Union[str, Path]] = None,
        override: bool = False,
        raise_on_error: bool = True,
        current_environment: Optional[str] = None,
        encoding: str = "utf-8",
    ):
        """
        Initialize DjangoEnv.

        Args:
            schema:               Dict mapping variable names to their schema definitions.
            load_file:            Whether to load a .env file. Default True.
            env_file:             Path (str or Path) to the .env file. Defaults to '.env'.
            override:             If True, .env values override existing env vars. Default False.
            raise_on_error:       If True, raises EnvValidationError on startup if required
                                  variables are missing or invalid. Default True.
            current_environment:  Name of the current environment (e.g. "production").
                                  Used to apply environment-specific rules.
            encoding:             File encoding. Default utf-8.
        """
        self._schema: Dict[str, EnvVarSchema] = self._build_schema(schema)
        self._current_environment = current_environment
        self._results: List[EnvVarResult] = []
        self._value_cache: Dict[str, Any] = {}

        # Load .env file if requested
        if load_file:
            load_env_file(
                filepath=env_file,
                override=override,
                encoding=encoding,
            )

        # Validate all variables
        self._results = validate_all(
            schema=self._schema,
            environ=dict(os.environ),
            current_environment=current_environment,
        )

        # Build value cache for quick access
        for result in self._results:
            if result.level == IssueLevel.OK:
                self._value_cache[result.name] = result.value

        # Raise on errors if configured
        if raise_on_error:
            issues = [r for r in self._results if r.has_issue]
            if issues:
                raise EnvValidationError(issues)

    def __call__(self, name: str, default: Any = None) -> Any:
        """
        Get a validated environment variable value.

        Args:
            name:    The name of the environment variable.
            default: Fallback value if the variable is not set (overrides schema default).

        Returns:
            The cast and validated value.
        """
        if name in self._value_cache:
            return self._value_cache[name]
        if default is not None:
            return default
        if name in self._schema:
            schema = self._schema[name]
            if schema.default is not None:
                return schema.default
        return None

    def get(self, name: str, default: Any = None) -> Any:
        """Alias for __call__. More explicit for some use cases."""
        return self(name, default)

    def str(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self(name, default)

    def int(self, name: str, default: Optional[int] = None) -> Optional[int]:
        return self(name, default)

    def bool(self, name: str, default: Optional[bool] = None) -> Optional[bool]:
        return self(name, default)

    def list(self, name: str, default: Optional[list] = None) -> Optional[list]:
        return self(name, default)

    def json(self, name: str, default: Any = None) -> Any:
        return self(name, default)

    @property
    def results(self) -> List[EnvVarResult]:
        """All validation results."""
        return self._results

    @property
    def issues(self) -> List[EnvVarResult]:
        """Only results that have issues."""
        return [r for r in self._results if r.has_issue]

    @property
    def is_valid(self) -> bool:
        """True if all required variables are set and valid."""
        return len(self.issues) == 0

    def report(
        self,
        use_color: bool = True,
        show_values: bool = False,
        output=None,
    ) -> None:
        """
        Print a formatted health report to stdout or a given output stream.

        Args:
            use_color:   Use ANSI colors. Default True.
            show_values: Show actual values (secrets always hidden). Default False.
            output:      Output stream. Defaults to sys.stdout.
        """
        if output is None:
            output = sys.stdout

        formatted = format_report(
            self._results,
            use_color=use_color,
            show_values=show_values,
            environment=self._current_environment,
        )
        output.write(formatted + "\n")

    def export_example(self, output_path: str = ".env.example", encoding: str = "utf-8") -> None:
        """
        Generate a .env.example file from the schema.

        Args:
            output_path: Path to write the example file. Default '.env.example'.
            encoding:    File encoding. Default utf-8.
        """
        generate_example_file(
            schema=self._schema,
            output_path=output_path,
            encoding=encoding,
        )

    @staticmethod
    def _build_schema(raw_schema: Dict[str, Union[Dict, EnvVarSchema]]) -> Dict[str, EnvVarSchema]:
        """Convert raw dict definitions to EnvVarSchema instances."""
        result = {}
        for name, definition in raw_schema.items():
            if isinstance(definition, EnvVarSchema):
                result[name] = definition
            elif isinstance(definition, dict):
                try:
                    result[name] = EnvVarSchema(**definition)
                except TypeError as e:
                    raise EnvSchemaError(
                        f"Invalid schema definition for '{name}': {e}"
                    )
            else:
                raise EnvSchemaError(
                    f"Schema for '{name}' must be a dict or EnvVarSchema, "
                    f"got {type(definition).__name__}"
                )
        return result
