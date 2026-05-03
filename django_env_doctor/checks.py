"""
Django system checks integration for django-env-doctor.

Registers env validation as Django system checks so issues
appear in `manage.py check` output.
"""

from typing import List, Optional

from .types import EnvVarResult, IssueLevel


def register_system_checks(results: List[EnvVarResult]) -> None:
    """
    Register env validation results as Django system checks.

    Call this from your AppConfig.ready() or at the bottom of settings.py
    after creating your DjangoEnv instance.
    """
    try:
        from django.core.checks import Error, Warning, register
    except ImportError:
        return  # Django not installed, skip silently

    @register(deploy=False)
    def env_doctor_checks(app_configs, **kwargs):
        messages = []
        for result in results:
            if result.level == IssueLevel.MISSING:
                messages.append(
                    Error(
                        f"Required environment variable '{result.name}' is not set.",
                        hint=f"Add {result.name} to your .env file or environment.",
                        id="env_doctor.E001",
                    )
                )
            elif result.level == IssueLevel.INVALID:
                messages.append(
                    Error(
                        f"Environment variable '{result.name}' has an invalid value: {result.message}",
                        hint=f"Check the value of {result.name} in your .env file.",
                        id="env_doctor.E002",
                    )
                )
            elif result.level == IssueLevel.WARN:
                messages.append(
                    Warning(
                        f"Environment variable '{result.name}': {result.message}",
                        id="env_doctor.W001",
                    )
                )
        return messages
