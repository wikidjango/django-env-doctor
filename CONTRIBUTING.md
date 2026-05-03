# Contributing to django-env-doctor

Thank you for taking the time to contribute. This document explains how to get
started and what to keep in mind when submitting changes.

---

## Setting up the development environment

```bash
git clone https://github.com/wikidjango/django-env-doctor
cd django-env-doctor
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

---

## Running the test suite

```bash
pytest
```

With coverage:

```bash
pytest --cov=django_env_doctor --cov-report=term-missing
```

---

## Code style

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting.

```bash
ruff check .
ruff format .
```

---

## Type checking

```bash
mypy django_env_doctor
```

---

## What to work on

Check the [issues](https://github.com/wikidjango/django-env-doctor/issues) page
for open issues labeled `good first issue` or `help wanted`.

Before starting work on a large feature, please open an issue to discuss it first.
This avoids duplicate effort and ensures the feature fits the project direction.

---

## Pull request checklist

- [ ] Tests added or updated for all changed behaviour
- [ ] All existing tests pass (`pytest`)
- [ ] Code passes linting (`ruff check .`)
- [ ] CHANGELOG.md updated under `[Unreleased]`
- [ ] Docstrings updated where relevant

---

## Design principles

- **Zero runtime dependencies.** The package should install with nothing extra.
- **Explicit over implicit.** Errors should be loud and clear, not silent.
- **DX first.** Every feature should make a developer's day measurably easier.
- **Small surface area.** Resist the urge to add features that belong in other tools.
