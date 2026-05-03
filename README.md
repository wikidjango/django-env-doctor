# django-env-doctor

> Validate, load, and report on Django environment variables — all in one place.

[![PyPI version](https://img.shields.io/pypi/v/django-env-doctor.svg)](https://pypi.org/project/django-env-doctor/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-env-doctor.svg)](https://pypi.org/project/django-env-doctor/)
[![Django versions](https://img.shields.io/pypi/djversions/django-env-doctor.svg)](https://pypi.org/project/django-env-doctor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The problem

Every Django developer has hit this at some point:

- App crashes at startup with `KeyError` because a new env var was added but not documented
- Teammate clones the repo and has no idea what goes in `.env`
- Deployment fails because an env var is set to `"true"` but the code expects a boolean
- You find out a required variable is missing only after the server is already live

**django-env-doctor** solves all of this with a single object in your `settings.py`.

---

## Features

- Load `.env` files into `os.environ`
- Declare all env variables in a single schema
- Type casting — `str`, `int`, `float`, `bool`, `url`, `email`, `json`, `list`, `path`
- Required field validation with a clear error at startup
- Default value support
- Validation rules — `min`, `max`, `min_length`, `max_length`, `choices`
- Reports **all** missing/invalid vars at once instead of failing one by one
- CLI command `manage.py env_doctor` with a clean health report
- CI-friendly exit codes — `0` for clean, `1` for issues
- Auto-generate `.env.example` from your schema (always in sync)
- Secret masking — sensitive values are never shown in logs or reports
- Optional loading — use as a validator-only on top of existing loaders
- Django system checks integration (`manage.py check`)
- Multi-environment support — different rules for `dev`, `staging`, `prod`
- **Zero runtime dependencies**

---

## Installation

```bash
pip install django-env-doctor
```

---

## Quick start

Replace the scattered `os.environ.get()` calls in your `settings.py` with one `DjangoEnv` instance:

```python
# settings.py
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
        "MAX_UPLOAD_MB": {
            "type": "int",
            "default": 10,
            "min": 1,
            "max": 100,
            "description": "Maximum file upload size in megabytes",
        },
        "ADMIN_EMAIL": {
            "type": "email",
            "required": False,
            "description": "Admin notification email",
        },
        "SENTRY_DSN": {
            "type": "url",
            "required": True,
            "environments": ["production", "staging"],
            "description": "Sentry error tracking DSN",
        },
    },
    load_file=True,       # Load .env file automatically
    env_file=".env",      # Path to .env file
    raise_on_error=True,  # Raise at startup if required vars are missing
)

# Use the validated values directly
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
MAX_UPLOAD_MB = env("MAX_UPLOAD_MB")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        # DATABASE_URL is validated and available
    }
}
```

---

## Schema definition

Each variable in the schema accepts the following options:

| Option         | Type            | Default  | Description                                               |
|----------------|-----------------|----------|-----------------------------------------------------------|
| `type`         | str             | `"str"`  | Variable type. See supported types below.                 |
| `required`     | bool            | `True`   | Whether the variable must be set.                         |
| `default`      | any             | `None`   | Default value if the variable is not set.                 |
| `description`  | str             | `""`     | Human-readable description. Used in `.env.example`.       |
| `secret`       | bool            | `False`  | If True, value is masked in reports and logs.             |
| `min_length`   | int             | `None`   | Minimum string or list length.                            |
| `max_length`   | int             | `None`   | Maximum string or list length.                            |
| `min`          | float           | `None`   | Minimum numeric value.                                    |
| `max`          | float           | `None`   | Maximum numeric value.                                    |
| `choices`      | list            | `None`   | Value must be one of the listed choices.                  |
| `environments` | list of str     | `None`   | Only validate this var in specific environments.          |

### Supported types

| Type      | Example value             | Python result       |
|-----------|---------------------------|---------------------|
| `str`     | `"hello"`                 | `"hello"`           |
| `int`     | `"42"`                    | `42`                |
| `float`   | `"3.14"`                  | `3.14`              |
| `bool`    | `"true"`, `"1"`, `"yes"`  | `True`              |
| `url`     | `"https://example.com"`   | `"https://example.com"` |
| `email`   | `"user@example.com"`      | `"user@example.com"` |
| `json`    | `'{"key": "val"}'`        | `{"key": "val"}`    |
| `list`    | `"a,b,c"` or `'["a","b"]'` | `["a", "b", "c"]` |
| `path`    | `"~/media"`               | `"/home/user/media"` |

---

## CLI health report

Run this any time to see the status of your environment:

```bash
python manage.py env_doctor
```

Example output:

```
django-env-doctor  [production]
------------------------------------------------------------
[  OK   ]  SECRET_KEY          *** hidden ***
[  OK   ]  DEBUG               → False (default)
[MISSING]  DATABASE_URL        Required variable is not set
[ SKIP  ]  ADMIN_EMAIL         Optional, not set
[INVALID]  MAX_UPLOAD_MB       Value must be <= 100
[  OK   ]  ALLOWED_HOSTS       → set

------------------------------------------------------------
Total: 6  OK: 3  Missing: 1  Invalid: 1  Warn: 0  Skip: 1
2 issue(s) found. Your app may not start correctly.
```

### Additional options

```bash
# Show actual values (secrets always hidden)
python manage.py env_doctor --show-values

# CI mode: plain text output, exit code 1 on issues
python manage.py env_doctor --ci

# Generate .env.example from your schema
python manage.py env_doctor --export-example

# Custom output path for example file
python manage.py env_doctor --export-example --example-output config/.env.example
```

---

## Generate .env.example automatically

```bash
python manage.py env_doctor --export-example
```

This generates a `.env.example` that stays in sync with your schema:

```bash
# .env.example
# Auto-generated by django-env-doctor
# Do NOT commit your actual .env file — only this example.

# Django secret key
# [type=str, required, secret]
SECRET_KEY=your-secret-secret-key

# Enable debug mode
# [type=bool, optional]
DEBUG=False

# Primary database connection URL
# [type=url, required]
DATABASE_URL=
```

---

## Use as validator only (no file loading)

If you already use `python-dotenv` or `django-environ` to load your `.env` file, you can use `django-env-doctor` purely for validation:

```python
env = DjangoEnv(
    schema={...},
    load_file=False,   # Don't load .env — just validate what's already in os.environ
    raise_on_error=True,
)
```

---

## Multi-environment support

Mark variables as only required in specific environments:

```python
env = DjangoEnv(
    schema={
        "SENTRY_DSN": {
            "type": "url",
            "required": True,
            "environments": ["production", "staging"],
        },
        "DEBUG": {
            "type": "bool",
            "default": False,
        },
    },
    current_environment=os.environ.get("DJANGO_ENV", "development"),
)
```

`SENTRY_DSN` will only be required when `DJANGO_ENV` is `production` or `staging`.

---

## Django system checks integration

```python
# settings.py or apps.py
from django_env_doctor import DjangoEnv, register_system_checks

env = DjangoEnv(schema={...}, raise_on_error=False)
register_system_checks(env.results)
```

Issues will now appear in `python manage.py check`:

```
SystemCheckError: System check identified some issues:

ERRORS:
?: (env_doctor.E001) Required environment variable 'DATABASE_URL' is not set.
        HINT: Add DATABASE_URL to your .env file or environment.
```

---

## CI integration

```bash
# In your CI pipeline
python manage.py env_doctor --ci
# Exits with code 1 if any required variables are missing or invalid
```

---

## Running tests

```bash
pip install -e ".[dev]"
pytest
pytest --cov=django_env_doctor
```

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Run the test suite (`pytest`)
5. Submit a pull request

---

## License

MIT — see [LICENSE](LICENSE) for details.
