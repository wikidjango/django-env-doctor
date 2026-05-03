"""
django-env-doctor
~~~~~~~~~~~~~~~~~

A Django environment variable validator, loader, and health reporter.

Basic usage::

    from django_env_doctor import DjangoEnv

    env = DjangoEnv(
        schema={
            "SECRET_KEY": {
                "type": "str",
                "required": True,
                "secret": True,
                "min_length": 40,
                "description": "Django secret key",
            },
            "DEBUG": {
                "type": "bool",
                "default": False,
                "description": "Enable debug mode",
            },
            "DATABASE_URL": {
                "type": "url",
                "required": True,
                "description": "Primary database connection URL",
            },
            "ALLOWED_HOSTS": {
                "type": "list",
                "default": [],
                "description": "Comma-separated list of allowed hosts",
            },
        },
        load_file=True,
        env_file=".env",
        raise_on_error=True,
    )

    SECRET_KEY = env("SECRET_KEY")
    DEBUG = env("DEBUG")
    DATABASE_URL = env("DATABASE_URL")

:copyright: (c) 2026 django.wiki (Ahmad)
:license: MIT
"""

__version__ = "0.1.0"
__author__ = "django.wiki (Ahmad)"
__license__ = "MIT"

from .checks import register_system_checks
from .env import DjangoEnv
from .exceptions import EnvCastError, EnvDoctorError, EnvSchemaError, EnvValidationError
from .types import EnvVarSchema, EnvVarType, IssueLevel

__all__ = [
    "DjangoEnv",
    "EnvVarSchema",
    "EnvVarType",
    "IssueLevel",
    "EnvDoctorError",
    "EnvCastError",
    "EnvValidationError",
    "EnvSchemaError",
    "register_system_checks",
]
