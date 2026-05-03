"""
Custom exceptions for django-env-doctor.
"""


class EnvDoctorError(Exception):
    """Base exception for django-env-doctor."""
    pass


class EnvCastError(EnvDoctorError):
    """Raised when a value cannot be cast to the expected type."""

    def __init__(self, name: str, raw_value: str, target_type, message: str):
        self.name = name
        self.raw_value = raw_value
        self.target_type = target_type
        self.message = message
        super().__init__(f"[{name}] {message}")


class EnvValidationError(EnvDoctorError):
    """Raised when one or more env variables fail validation."""

    def __init__(self, issues: list):
        self.issues = issues
        count = len(issues)
        lines = "\n".join(f"  - {i.name}: {i.message}" for i in issues)
        super().__init__(
            f"\ndjango-env-doctor found {count} issue(s):\n{lines}\n\n"
            f"Run `python manage.py env_doctor` for a full report."
        )


class EnvSchemaError(EnvDoctorError):
    """Raised when the schema definition itself is invalid."""
    pass
