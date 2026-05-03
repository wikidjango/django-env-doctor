"""
Example Django settings.py using django-env-doctor.

This shows a realistic production-ready settings file.
"""

import os
from pathlib import Path

from django_env_doctor import DjangoEnv, register_system_checks

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------

env = DjangoEnv(
    schema={
        # Core Django
        "SECRET_KEY": {
            "type": "str",
            "required": True,
            "secret": True,
            "min_length": 40,
            "description": "Django secret key — generate with: python -c \"import secrets; print(secrets.token_urlsafe(50))\"",
        },
        "DEBUG": {
            "type": "bool",
            "default": False,
            "description": "Enable debug mode. Never True in production.",
        },
        "DJANGO_ENV": {
            "type": "str",
            "default": "development",
            "choices": ["development", "staging", "production"],
            "description": "Current environment name.",
        },
        "ALLOWED_HOSTS": {
            "type": "list",
            "default": [],
            "description": "Comma-separated list of allowed hostnames.",
        },

        # Database
        "DATABASE_URL": {
            "type": "url",
            "required": True,
            "description": "Database connection URL. e.g. postgres://user:pass@localhost:5432/mydb",
        },

        # Cache
        "REDIS_URL": {
            "type": "url",
            "default": "redis://localhost:6379/0",
            "description": "Redis connection URL for cache and Celery.",
        },

        # Email
        "EMAIL_HOST": {
            "type": "str",
            "required": False,
            "description": "SMTP host for outgoing email.",
        },
        "EMAIL_PORT": {
            "type": "int",
            "default": 587,
            "min": 1,
            "max": 65535,
            "description": "SMTP port.",
        },
        "EMAIL_HOST_USER": {
            "type": "str",
            "required": False,
            "description": "SMTP username.",
        },
        "EMAIL_HOST_PASSWORD": {
            "type": "str",
            "required": False,
            "secret": True,
            "description": "SMTP password.",
        },
        "DEFAULT_FROM_EMAIL": {
            "type": "email",
            "default": "noreply@example.com",
            "description": "Default sender email address.",
        },

        # Storage
        "AWS_ACCESS_KEY_ID": {
            "type": "str",
            "required": True,
            "secret": True,
            "environments": ["production", "staging"],
            "description": "AWS access key for S3 storage.",
        },
        "AWS_SECRET_ACCESS_KEY": {
            "type": "str",
            "required": True,
            "secret": True,
            "environments": ["production", "staging"],
            "description": "AWS secret key for S3 storage.",
        },
        "AWS_STORAGE_BUCKET_NAME": {
            "type": "str",
            "required": True,
            "environments": ["production", "staging"],
            "description": "S3 bucket name for media and static files.",
        },

        # Monitoring
        "SENTRY_DSN": {
            "type": "url",
            "required": True,
            "environments": ["production", "staging"],
            "description": "Sentry error tracking DSN.",
        },

        # App-specific
        "MAX_UPLOAD_MB": {
            "type": "int",
            "default": 10,
            "min": 1,
            "max": 100,
            "description": "Maximum file upload size in megabytes.",
        },
        "FEATURE_FLAGS": {
            "type": "json",
            "default": {},
            "description": "JSON object of feature flags. e.g. {\"new_ui\": true}",
        },
    },
    load_file=True,
    env_file=BASE_DIR / ".env",
    raise_on_error=True,
    current_environment=os.environ.get("DJANGO_ENV", "development"),
)

# Register env results as Django system checks
register_system_checks(env.results)

# ---------------------------------------------------------------------------
# Django settings using validated env values
# ---------------------------------------------------------------------------

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        # Parse DATABASE_URL yourself or use dj-database-url
        # "NAME": ...,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

MAX_UPLOAD_MB = env("MAX_UPLOAD_MB")
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_MB * 1024 * 1024

FEATURE_FLAGS = env("FEATURE_FLAGS")
