"""
Tests for django-env-doctor.

Run with: pytest
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Allow running tests without installing the package (e.g. python -m pytest from project root)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from django_env_doctor.caster import cast_value
from django_env_doctor.env import DjangoEnv
from django_env_doctor.exceptions import EnvCastError, EnvSchemaError, EnvValidationError
from django_env_doctor.loader import _parse_env_content, generate_example_file, load_env_file
from django_env_doctor.reporter import format_report
from django_env_doctor.types import EnvVarResult, EnvVarSchema, EnvVarType, IssueLevel
from django_env_doctor.validator import validate_all, validate_one


# ---------------------------------------------------------------------------
# Caster tests
# ---------------------------------------------------------------------------


class TestCaster:
    def test_cast_str(self):
        assert cast_value("hello", EnvVarType.STR, "VAR") == "hello"

    def test_cast_int_valid(self):
        assert cast_value("42", EnvVarType.INT, "VAR") == 42

    def test_cast_int_invalid(self):
        with pytest.raises(EnvCastError):
            cast_value("not-a-number", EnvVarType.INT, "VAR")

    def test_cast_float_valid(self):
        assert cast_value("3.14", EnvVarType.FLOAT, "VAR") == 3.14

    def test_cast_float_invalid(self):
        with pytest.raises(EnvCastError):
            cast_value("pi", EnvVarType.FLOAT, "VAR")

    @pytest.mark.parametrize("raw,expected", [
        ("true", True), ("True", True), ("TRUE", True),
        ("1", True), ("yes", True), ("on", True),
        ("false", False), ("False", False), ("FALSE", False),
        ("0", False), ("no", False), ("off", False),
    ])
    def test_cast_bool_valid(self, raw, expected):
        assert cast_value(raw, EnvVarType.BOOL, "VAR") == expected

    def test_cast_bool_invalid(self):
        with pytest.raises(EnvCastError):
            cast_value("maybe", EnvVarType.BOOL, "VAR")

    def test_cast_url_valid(self):
        assert cast_value("https://example.com", EnvVarType.URL, "VAR") == "https://example.com"

    def test_cast_url_invalid(self):
        with pytest.raises(EnvCastError):
            cast_value("not-a-url", EnvVarType.URL, "VAR")

    def test_cast_email_valid(self):
        assert cast_value("user@example.com", EnvVarType.EMAIL, "VAR") == "user@example.com"

    def test_cast_email_invalid(self):
        with pytest.raises(EnvCastError):
            cast_value("not-an-email", EnvVarType.EMAIL, "VAR")

    def test_cast_json_valid(self):
        result = cast_value('{"key": "value"}', EnvVarType.JSON, "VAR")
        assert result == {"key": "value"}

    def test_cast_json_invalid(self):
        with pytest.raises(EnvCastError):
            cast_value("{bad json}", EnvVarType.JSON, "VAR")

    def test_cast_list_comma_separated(self):
        result = cast_value("a,b,c", EnvVarType.LIST, "VAR")
        assert result == ["a", "b", "c"]

    def test_cast_list_json_array(self):
        result = cast_value('["a", "b"]', EnvVarType.LIST, "VAR")
        assert result == ["a", "b"]

    def test_cast_list_strips_spaces(self):
        result = cast_value("a, b, c", EnvVarType.LIST, "VAR")
        assert result == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------


class TestValidator:
    def test_required_variable_missing(self):
        schema = EnvVarSchema(type=EnvVarType.STR, required=True)
        result = validate_one("MY_VAR", schema, {}, None)
        assert result.level == IssueLevel.MISSING

    def test_required_variable_present(self):
        schema = EnvVarSchema(type=EnvVarType.STR, required=True)
        result = validate_one("MY_VAR", schema, {"MY_VAR": "hello"}, None)
        assert result.level == IssueLevel.OK
        assert result.value == "hello"

    def test_optional_variable_missing(self):
        schema = EnvVarSchema(type=EnvVarType.STR, required=False)
        result = validate_one("MY_VAR", schema, {}, None)
        assert result.level == IssueLevel.SKIP

    def test_default_value_used_when_missing(self):
        schema = EnvVarSchema(type=EnvVarType.BOOL, default=False)
        result = validate_one("DEBUG", schema, {}, None)
        assert result.level == IssueLevel.OK
        assert result.value is False

    def test_type_cast_failure(self):
        schema = EnvVarSchema(type=EnvVarType.INT, required=True)
        result = validate_one("PORT", schema, {"PORT": "not-a-number"}, None)
        assert result.level == IssueLevel.INVALID

    def test_min_length_rule_pass(self):
        schema = EnvVarSchema(type=EnvVarType.STR, required=True, min_length=5)
        result = validate_one("KEY", schema, {"KEY": "hello123"}, None)
        assert result.level == IssueLevel.OK

    def test_min_length_rule_fail(self):
        schema = EnvVarSchema(type=EnvVarType.STR, required=True, min_length=50)
        result = validate_one("KEY", schema, {"KEY": "short"}, None)
        assert result.level == IssueLevel.INVALID

    def test_choices_rule_pass(self):
        schema = EnvVarSchema(type=EnvVarType.STR, choices=["dev", "prod", "staging"])
        result = validate_one("ENV", schema, {"ENV": "dev"}, None)
        assert result.level == IssueLevel.OK

    def test_choices_rule_fail(self):
        schema = EnvVarSchema(type=EnvVarType.STR, choices=["dev", "prod"])
        result = validate_one("ENV", schema, {"ENV": "unknown"}, None)
        assert result.level == IssueLevel.INVALID

    def test_min_numeric_rule(self):
        schema = EnvVarSchema(type=EnvVarType.INT, required=True, min=1)
        result = validate_one("PORT", schema, {"PORT": "0"}, None)
        assert result.level == IssueLevel.INVALID

    def test_max_numeric_rule(self):
        schema = EnvVarSchema(type=EnvVarType.INT, required=True, max=65535)
        result = validate_one("PORT", schema, {"PORT": "99999"}, None)
        assert result.level == IssueLevel.INVALID

    def test_environment_filter_skip(self):
        schema = EnvVarSchema(type=EnvVarType.STR, required=True, environments=["production"])
        result = validate_one("SENTRY_DSN", schema, {}, current_environment="development")
        assert result.level == IssueLevel.SKIP

    def test_environment_filter_applies(self):
        schema = EnvVarSchema(type=EnvVarType.STR, required=True, environments=["production"])
        result = validate_one("SENTRY_DSN", schema, {}, current_environment="production")
        assert result.level == IssueLevel.MISSING

    def test_validate_all(self):
        schema = {
            "SECRET_KEY": EnvVarSchema(type=EnvVarType.STR, required=True),
            "DEBUG": EnvVarSchema(type=EnvVarType.BOOL, default=False),
        }
        results = validate_all(schema, {"SECRET_KEY": "my-secret-key"})
        assert len(results) == 2
        levels = {r.name: r.level for r in results}
        assert levels["SECRET_KEY"] == IssueLevel.OK
        assert levels["DEBUG"] == IssueLevel.OK


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------


class TestLoader:
    def test_parse_simple_key_value(self):
        content = "KEY=value"
        result = _parse_env_content(content)
        assert result == {"KEY": "value"}

    def test_parse_ignores_comments(self):
        content = "# This is a comment\nKEY=value"
        result = _parse_env_content(content)
        assert result == {"KEY": "value"}

    def test_parse_quoted_values(self):
        content = 'KEY="hello world"'
        result = _parse_env_content(content)
        assert result == {"KEY": "hello world"}

    def test_parse_single_quoted_values(self):
        content = "KEY='hello world'"
        result = _parse_env_content(content)
        assert result == {"KEY": "hello world"}

    def test_parse_strips_inline_comments(self):
        content = "KEY=value  # inline comment"
        result = _parse_env_content(content)
        assert result == {"KEY": "value"}

    def test_parse_export_prefix(self):
        content = "export KEY=value"
        result = _parse_env_content(content)
        assert result == {"KEY": "value"}

    def test_parse_blank_lines(self):
        content = "\nKEY=value\n\nOTHER=thing\n"
        result = _parse_env_content(content)
        assert result == {"KEY": "value", "OTHER": "thing"}

    def test_load_env_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_LOAD_KEY=testvalue123\n")
            filepath = f.name

        try:
            # Ensure it's not already set
            os.environ.pop("TEST_LOAD_KEY", None)
            loaded = load_env_file(filepath=filepath)
            assert "TEST_LOAD_KEY" in loaded
            assert os.environ.get("TEST_LOAD_KEY") == "testvalue123"
        finally:
            os.unlink(filepath)
            os.environ.pop("TEST_LOAD_KEY", None)

    def test_load_env_file_no_override(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_OVERRIDE=from_file\n")
            filepath = f.name

        try:
            os.environ["TEST_OVERRIDE"] = "from_env"
            load_env_file(filepath=filepath, override=False)
            assert os.environ.get("TEST_OVERRIDE") == "from_env"
        finally:
            os.unlink(filepath)
            os.environ.pop("TEST_OVERRIDE", None)

    def test_generate_example_file(self):
        from django_env_doctor.types import EnvVarSchema, EnvVarType

        schema = {
            "SECRET_KEY": EnvVarSchema(
                type=EnvVarType.STR,
                required=True,
                secret=True,
                description="Django secret key",
            ),
            "DEBUG": EnvVarSchema(type=EnvVarType.BOOL, default=False),
        }

        with tempfile.NamedTemporaryFile(suffix=".env.example", delete=False) as f:
            output_path = f.name

        try:
            generate_example_file(schema, output_path=output_path)
            content = Path(output_path).read_text()
            assert "SECRET_KEY" in content
            assert "DEBUG" in content
            assert "Auto-generated" in content
        finally:
            os.unlink(output_path)


# ---------------------------------------------------------------------------
# DjangoEnv integration tests
# ---------------------------------------------------------------------------


class TestDjangoEnv:
    def test_basic_usage(self):
        with patch.dict(os.environ, {"MY_SECRET": "supersecretkey1234567890abcdef"}):
            env = DjangoEnv(
                schema={"MY_SECRET": {"type": "str", "required": True}},
                load_file=False,
                raise_on_error=True,
            )
            assert env("MY_SECRET") == "supersecretkey1234567890abcdef"

    def test_raises_on_missing_required(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvValidationError):
                DjangoEnv(
                    schema={"REQUIRED_VAR": {"type": "str", "required": True}},
                    load_file=False,
                    raise_on_error=True,
                )

    def test_no_raise_on_error_false(self):
        with patch.dict(os.environ, {}, clear=True):
            env = DjangoEnv(
                schema={"REQUIRED_VAR": {"type": "str", "required": True}},
                load_file=False,
                raise_on_error=False,
            )
            assert not env.is_valid

    def test_default_values(self):
        with patch.dict(os.environ, {}, clear=True):
            env = DjangoEnv(
                schema={"DEBUG": {"type": "bool", "default": False}},
                load_file=False,
                raise_on_error=False,
            )
            assert env("DEBUG") is False

    def test_invalid_schema_key(self):
        with pytest.raises(EnvSchemaError):
            DjangoEnv(
                schema={"VAR": {"type": "str", "unknown_field": True}},
                load_file=False,
                raise_on_error=False,
            )

    def test_is_valid_true(self):
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            env = DjangoEnv(
                schema={"MY_VAR": {"type": "str", "required": True}},
                load_file=False,
                raise_on_error=False,
            )
            assert env.is_valid

    def test_typed_accessors(self):
        with patch.dict(os.environ, {"MY_INT": "42"}):
            env = DjangoEnv(
                schema={"MY_INT": {"type": "int", "required": True}},
                load_file=False,
                raise_on_error=False,
            )
            assert env.int("MY_INT") == 42

    def test_secret_value_in_results(self):
        with patch.dict(os.environ, {"SECRET_KEY": "my-very-secret-key-that-is-long-enough"}):
            env = DjangoEnv(
                schema={
                    "SECRET_KEY": {
                        "type": "str",
                        "required": True,
                        "secret": True,
                        "min_length": 10,
                    }
                },
                load_file=False,
                raise_on_error=False,
            )
            result = next(r for r in env.results if r.name == "SECRET_KEY")
            assert result.level == IssueLevel.OK
            assert result.schema.secret is True


# ---------------------------------------------------------------------------
# Reporter tests
# ---------------------------------------------------------------------------


class TestReporter:
    def test_format_report_no_color(self):
        results = [
            EnvVarResult(
                name="MY_VAR",
                level=IssueLevel.OK,
                value="hello",
                schema=EnvVarSchema(type=EnvVarType.STR),
            ),
            EnvVarResult(
                name="MISSING_VAR",
                level=IssueLevel.MISSING,
                message="Required variable is not set",
                schema=EnvVarSchema(type=EnvVarType.STR, required=True),
            ),
        ]
        report = format_report(results, use_color=False)
        assert "MY_VAR" in report
        assert "MISSING_VAR" in report
        assert "OK" in report
        assert "MISSING" in report

    def test_format_report_summary_counts(self):
        results = [
            EnvVarResult(name="A", level=IssueLevel.OK, schema=EnvVarSchema()),
            EnvVarResult(name="B", level=IssueLevel.MISSING, schema=EnvVarSchema()),
            EnvVarResult(name="C", level=IssueLevel.INVALID, schema=EnvVarSchema()),
        ]
        report = format_report(results, use_color=False)
        assert "1 issue" in report or "2 issue" in report

    def test_secret_hidden_in_report(self):
        results = [
            EnvVarResult(
                name="SECRET",
                level=IssueLevel.OK,
                value="super-secret",
                raw_value="super-secret",
                schema=EnvVarSchema(type=EnvVarType.STR, secret=True),
            )
        ]
        report = format_report(results, use_color=False, show_values=True)
        assert "super-secret" not in report
        assert "hidden" in report
