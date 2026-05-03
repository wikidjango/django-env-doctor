# Changelog

All notable changes to django-env-doctor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-01

### Added
- Initial release
- `DjangoEnv` class for schema-based env validation and loading
- Type casting for `str`, `int`, `float`, `bool`, `url`, `email`, `json`, `list`, `path`
- Validation rules: `required`, `default`, `min_length`, `max_length`, `min`, `max`, `choices`
- `.env` file loading with comment, quote, and inline comment support
- CLI command `manage.py env_doctor` with colored health report
- `--export-example` flag for auto-generating `.env.example`
- `--ci` flag for plain output and exit code support
- `--show-values` flag for debugging
- Secret masking for sensitive variables
- Multi-environment support via `environments` field
- Django system checks integration via `register_system_checks()`
- Zero runtime dependencies
