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


def has_tests(root: Path) -> bool:
    """Tell whether at least one test file exists under the tests folder."""
    return any((root / TESTS_DIR).rglob(TEST_FILE_PATTERN))


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
    exit_code = run_tests(ROOT)
    if exit_code != 0:
        logger.error("The tests failed (exit code %d).", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
