"""Unit tests of the milestone runner's coverage step (docs/workflow.md, Execute, step 4)."""

import importlib.util
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO / "scripts" / "milestones-runner.py"
COVERAGE_PATH = REPO / "scripts" / "spec_coverage.py"

SPECS = """# Specs

| ID | Type | Requirement |
| --- | --- | --- |
| FR-01 | E | When the user does a thing, the system shall do it. |
| NFR-01 | U | The system shall look fine. |
"""

TEST_FILE = "def test_fr_01_does_the_thing():\n    assert True\n"

PLAN_WITH_HUMAN_CHECKS = """# Plan

## Milestones

## Human checks

- NFR-01: open the page and look at it.
"""

PLAN_WITHOUT_HUMAN_CHECKS = "# Plan\n\n## Milestones\n"

BLOCK = [
    "### M99 — Invented",
    "",
    "- **Refs:** FR-01, NFR-01.",
    "- **Tests first:** unit: test_fr_01_does_the_thing.",
    "- **Gate:** none.",
]


def load_runner():
    """Load scripts/milestones-runner.py by path; register it first, as it defines data classes."""
    spec = importlib.util.spec_from_file_location("milestones_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["milestones_runner"] = module
    spec.loader.exec_module(module)
    return module


def make_root(tmp_path, plan_text):
    """Build a temporary root with the coverage script, a spec, one test file and a plan."""
    (tmp_path / "scripts").mkdir()
    shutil.copy(COVERAGE_PATH, tmp_path / "scripts" / "spec_coverage.py")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "specs.md").write_text(SPECS, encoding="utf-8")
    (tmp_path / "docs" / "plan.md").write_text(plan_text, encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_thing.py").write_text(TEST_FILE, encoding="utf-8")
    return tmp_path


def test_runner_coverage_counts_an_id_of_human_checks_as_manual(tmp_path):
    root = make_root(tmp_path, PLAN_WITH_HUMAN_CHECKS)

    assert load_runner().coverage_problem(root, 99, BLOCK) is None


def test_runner_coverage_still_fails_an_id_without_test_or_manual_entry(tmp_path):
    root = make_root(tmp_path, PLAN_WITHOUT_HUMAN_CHECKS)

    problem = load_runner().coverage_problem(root, 99, BLOCK)

    assert problem is not None
    assert "NFR-01" in problem
