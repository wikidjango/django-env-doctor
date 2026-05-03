"""
Report formatting for django-env-doctor CLI output.
"""

from typing import List, Optional

from .types import EnvVarResult, IssueLevel

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"
WHITE = "\033[37m"

LEVEL_COLORS = {
    IssueLevel.OK: GREEN,
    IssueLevel.MISSING: RED,
    IssueLevel.INVALID: RED,
    IssueLevel.WARN: YELLOW,
    IssueLevel.SKIP: DIM,
}

LEVEL_LABELS = {
    IssueLevel.OK: "  OK   ",
    IssueLevel.MISSING: "MISSING",
    IssueLevel.INVALID: "INVALID",
    IssueLevel.WARN: " WARN  ",
    IssueLevel.SKIP: " SKIP  ",
}


def format_report(
    results: List[EnvVarResult],
    use_color: bool = True,
    show_values: bool = False,
    environment: Optional[str] = None,
) -> str:
    """
    Format validation results into a human-readable CLI report.

    Args:
        results:      List of EnvVarResult from the validator.
        use_color:    Whether to use ANSI color codes. Default True.
        show_values:  Whether to print actual values (never shown for secrets). Default False.
        environment:  The current environment name (e.g. "production").
    """
    lines = []

    # Header
    lines.append(_header(use_color, environment))
    lines.append("")

    # Variable rows
    name_width = max((len(r.name) for r in results), default=20) + 2

    for result in results:
        line = _format_row(result, name_width, use_color, show_values)
        lines.append(line)

    lines.append("")

    # Summary
    lines.append(_summary(results, use_color))

    return "\n".join(lines)


def _header(use_color: bool, environment: Optional[str]) -> str:
    title = "django-env-doctor"
    env_tag = f"  [{environment}]" if environment else ""
    separator = "-" * 60

    if use_color:
        return (
            f"{BOLD}{CYAN}{title}{RESET}{DIM}{env_tag}{RESET}\n"
            f"{DIM}{separator}{RESET}"
        )
    return f"{title}{env_tag}\n{separator}"


def _format_row(
    result: EnvVarResult,
    name_width: int,
    use_color: bool,
    show_values: bool,
) -> str:
    level_label = LEVEL_LABELS[result.level]
    color = LEVEL_COLORS[result.level] if use_color else ""
    reset = RESET if use_color else ""
    dim = DIM if use_color else ""

    name_col = result.name.ljust(name_width)

    # Value display
    if result.level == IssueLevel.OK:
        if result.schema and result.schema.secret:
            value_display = "*** hidden ***"
        elif result.value is None:
            value_display = "(not set)"
        elif show_values:
            value_display = f"→ {result.value}"
        else:
            value_display = "→ set"

        if result.message == "Using default value":
            value_display += f" {dim}(default){reset}"
    elif result.level == IssueLevel.SKIP:
        value_display = f"{dim}{result.message}{reset}"
    else:
        value_display = result.message

    return f"{color}[{level_label}]{reset}  {name_col} {value_display}"


def _summary(results: List[EnvVarResult], use_color: bool) -> str:
    separator = "-" * 60
    total = len(results)
    ok = sum(1 for r in results if r.level == IssueLevel.OK)
    missing = sum(1 for r in results if r.level == IssueLevel.MISSING)
    invalid = sum(1 for r in results if r.level == IssueLevel.INVALID)
    warn = sum(1 for r in results if r.level == IssueLevel.WARN)
    skip = sum(1 for r in results if r.level == IssueLevel.SKIP)

    issues = missing + invalid + warn
    reset = RESET if use_color else ""
    dim = DIM if use_color else ""
    bold = BOLD if use_color else ""

    lines = [f"{dim}{separator}{reset}"]

    stats = (
        f"{bold}Total:{reset} {total}  "
        f"{GREEN if use_color else ''}OK: {ok}{reset}  "
        f"{RED if use_color else ''}Missing: {missing}{reset}  "
        f"{RED if use_color else ''}Invalid: {invalid}{reset}  "
        f"{YELLOW if use_color else ''}Warn: {warn}{reset}  "
        f"{dim}Skip: {skip}{reset}"
    )
    lines.append(stats)

    if issues == 0:
        msg = f"{GREEN if use_color else ''}{bold}All checks passed.{reset}"
    else:
        msg = (
            f"{RED if use_color else ''}{bold}"
            f"{issues} issue(s) found. Your app may not start correctly.{reset}"
        )
    lines.append(msg)

    return "\n".join(lines)


def format_ci_summary(results: List[EnvVarResult]) -> str:
    """Plain text summary suitable for CI logs (no color)."""
    return format_report(results, use_color=False)
