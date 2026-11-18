"""Run the project's checks: the tests under tests/.

The git pre-commit hook (.githooks/pre-commit) runs the same. The tests run with pytest, the test
tool of the test policy in docs/design.md (D-30). When no test file exists, the check passes and
says so.

Run, after `conda activate design-kb`:
    python scripts/check.py
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("check")

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = "tests"
TEST_FILE_PATTERN = "test_*.py"
DOCS_PREFIX = "docs/"


def has_tests(root: Path) -> bool:
    """Tell whether at least one test file exists under the tests folder."""
    return any((root / TESTS_DIR).rglob(TEST_FILE_PATTERN))


def needs_tests(staged_paths: list[str]) -> bool:
    """Tell whether the tests must run: always, unless every staged path is under docs/."""
    if not staged_paths:
        return True
    return not all(path.startswith(DOCS_PREFIX) for path in staged_paths)


def staged_files(root: Path) -> list[str]:
    """Return the staged paths; a moved file lists both its old and its new path."""
    command = ["git", "diff", "--cached", "--name-only", "--no-renames"]
    result = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
    return result.stdout.splitlines() if result.returncode == 0 else []


def run_tests(root: Path) -> int:
    """Run every test with pytest from the repository root, and return the exit code."""
    command = [sys.executable, "-m", "pytest", TESTS_DIR]
    return subprocess.run(command, cwd=root, check=False).returncode


def main() -> int:
    """Run the tests when there are any. Return 0 when the checks pass."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    if not has_tests(ROOT):
        logger.info("No test file in %s/ yet: nothing to check.", TESTS_DIR)
        return 0
    if not needs_tests(staged_files(ROOT)):
        logger.info("Only files under %s are staged: tests skipped.", DOCS_PREFIX)
        return 0
    exit_code = run_tests(ROOT)
    if exit_code != 0:
        logger.error("The tests failed (exit code %d).", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
