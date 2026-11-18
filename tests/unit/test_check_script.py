"""Unit tests of the pre-commit check script (docs/design.md, D-30, Test policy)."""

import importlib.util
from pathlib import Path

CHECK_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check.py"


def load_check():
    """Load scripts/check.py by path, because scripts/ is not a package."""
    spec = importlib.util.spec_from_file_location("check_script", CHECK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_skips_tests_when_only_docs_staged():
    assert load_check().needs_tests(["docs/plan.md", "docs/specs.md"]) is False


def test_check_runs_tests_when_code_staged():
    assert load_check().needs_tests(["docs/plan.md", "src/app.py"]) is True


def test_check_runs_tests_when_nothing_staged():
    assert load_check().needs_tests([]) is True
