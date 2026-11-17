"""List which spec IDs have a test, and check the spec IDs of one milestone.

A spec ID is a requirement (FR-NN, NFR-NN) or an acceptance criterion (AC-NN) of docs/specs.md.
Each spec ID has one state:

- tested: a test function under tests/ has the ID in its name (FR-23 is `test_fr_23_...`).
- manual: a `Manual:` entry of a milestone block, or the section "Human checks" of docs/plan.md,
  names the ID.
- planned: the Refs of a milestone block in docs/plan.md name the ID.
- missing: none of these.

Without an argument, it lists every spec ID with its state. With `M<n>`, it checks the spec IDs in
the Refs of that milestone's block: each must be in the spec, and be tested or manual
(docs/workflow.md, Execute). It only reads files.

Run:
    python scripts/spec_coverage.py [M<n>] [--root FOLDER]
"""

import argparse
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("spec_coverage")

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = Path("docs") / "specs.md"
PLAN_PATH = Path("docs") / "plan.md"
TESTS_DIR = "tests"
TEST_FILE_PATTERN = "test_*.py"

# The IDs of docs/specs.md that a milestone can deliver. Design decisions (D-NN) and assumptions
# (A-NN) are not spec IDs.
SPEC_ID = re.compile(r"\b(?:FR|NFR|AC)-\d{2,}\b")
SPEC_ROW = re.compile(r"^\|\s*((?:FR|NFR|AC)-\d{2,})\s*\|")
TEST_NAME = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)", re.MULTILINE)
MANUAL_ENTRY = re.compile(r"Manual:((?:[\s,`]|and|(?:FR|NFR|AC)-\d{2,})+)")
MILESTONE_ARGUMENT = re.compile(r"M(\d+)", re.IGNORECASE)
MILESTONE_HEADING = re.compile(r"^### M(\d+)\b")
HUMAN_CHECKS_HEADING = re.compile(r"^## Human checks", re.IGNORECASE)
ANY_HEADING = re.compile(r"^#{1,3} ")
ENTRY_START = re.compile(r"^- \*\*")
WITHDRAWN = "withdrawn"

STATE_TESTED = "tested"
STATE_MANUAL = "manual"
STATE_PLANNED = "planned"
STATE_MISSING = "missing"
STATE_UNKNOWN = "not in the spec"
COVERED_STATES = (STATE_TESTED, STATE_MANUAL)

EXIT_OK = 0
EXIT_NOT_COVERED = 1
EXIT_USAGE = 2


@dataclass(frozen=True)
class Coverage:
    """Holds what the spec, the tests and the plan say about the spec IDs. Gives each a state."""

    spec_ids: list[str]
    tested: set[str]
    manual: set[str]
    planned: set[str]

    def state(self, spec_id: str) -> str:
        """Return the state of one spec ID: tested, manual, planned, missing or not in the spec."""
        if spec_id not in self.spec_ids:
            return STATE_UNKNOWN
        if spec_id in self.tested:
            return STATE_TESTED
        if spec_id in self.manual:
            return STATE_MANUAL
        if spec_id in self.planned:
            return STATE_PLANNED
        return STATE_MISSING


def read_lines(path: Path) -> list[str]:
    """Return the lines of a UTF-8 file, or no lines when the file does not exist."""
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8-sig").splitlines()


def unique(ids: list[str]) -> list[str]:
    """Return the IDs in their order, without duplicates."""
    return list(dict.fromkeys(ids))


def spec_ids_of(spec_lines: list[str]) -> list[str]:
    """Return the ID of each requirement and criterion row of the spec, without withdrawn rows."""
    ids = []
    for line in spec_lines:
        match = SPEC_ROW.match(line)
        cells = [cell.strip().lower() for cell in line.split("|")]
        if match is not None and WITHDRAWN not in cells:
            ids.append(match[1])
    return unique(ids)


def test_names_in(tests_dir: Path) -> list[str]:
    """Return the name of every test function in the test files under tests_dir."""
    names: list[str] = []
    if not tests_dir.is_dir():
        return names
    for path in sorted(tests_dir.rglob(TEST_FILE_PATTERN)):
        names.extend(TEST_NAME.findall(path.read_text(encoding="utf-8-sig")))
    return names


def name_has_id(name: str, spec_id: str) -> bool:
    """Tell whether a test name carries the spec ID: FR-23 is `fr_23`, and not part of `nfr_23`."""
    token = spec_id.lower().replace("-", "_")
    return re.search(rf"(?<![a-z0-9]){token}(?![0-9])", name) is not None


def tested_ids(spec_ids: list[str], test_names: list[str]) -> set[str]:
    """Return the spec IDs that at least one test name carries."""
    return {
        spec_id for spec_id in spec_ids if any(name_has_id(name, spec_id) for name in test_names)
    }


def milestone_blocks(plan_lines: list[str]) -> dict[int, list[str]]:
    """Return the lines of each `### M<n>` block of the plan, by milestone number."""
    blocks: dict[int, list[str]] = {}
    current: list[str] | None = None
    for line in plan_lines:
        if ANY_HEADING.match(line):
            match = MILESTONE_HEADING.match(line)
            current = blocks.setdefault(int(match[1]), []) if match is not None else None
        if current is not None:
            current.append(line)
    return blocks


def entry_text(block: list[str], label: str) -> str:
    """Return the text of the `- **<label>:**` entry of a block, with its continuation lines."""
    start = f"- **{label}:**"
    lines: list[str] = []
    for line in block:
        if line.startswith(start):
            lines = [line]
        elif lines and (ENTRY_START.match(line) or not line.strip()):
            break
        elif lines:
            lines.append(line)
    return " ".join(lines)


def refs_ids(block: list[str]) -> list[str]:
    """Return the spec IDs in the Refs entry of a milestone block."""
    return unique(SPEC_ID.findall(entry_text(block, "Refs")))


def manual_ids(block: list[str]) -> list[str]:
    """Return the spec IDs that the `Manual:` parts of the Tests first entry name."""
    parts = MANUAL_ENTRY.findall(entry_text(block, "Tests first"))
    return unique([spec_id for part in parts for spec_id in SPEC_ID.findall(part)])


def human_check_ids(plan_lines: list[str]) -> list[str]:
    """Return the spec IDs in the section "Human checks" of the plan."""
    ids: list[str] = []
    inside = False
    for line in plan_lines:
        if ANY_HEADING.match(line):
            inside = HUMAN_CHECKS_HEADING.match(line) is not None
        elif inside:
            ids.extend(SPEC_ID.findall(line))
    return unique(ids)


def read_coverage(root: Path, blocks: dict[int, list[str]], plan_lines: list[str]) -> Coverage:
    """Read the spec and the tests under root, and join them with the plan's blocks."""
    spec_ids = spec_ids_of(read_lines(root / SPEC_PATH))
    manual = set(human_check_ids(plan_lines))
    planned: set[str] = set()
    for block in blocks.values():
        manual.update(manual_ids(block))
        planned.update(refs_ids(block))
    tested = tested_ids(spec_ids, test_names_in(root / TESTS_DIR))
    return Coverage(spec_ids, tested, manual, planned)


def list_all(coverage: Coverage) -> int:
    """Log every spec ID with its state, then the count of each state. It always passes."""
    counts: dict[str, int] = {}
    for spec_id in coverage.spec_ids:
        state = coverage.state(spec_id)
        counts[state] = counts.get(state, 0) + 1
        logger.info("%-7s %s", spec_id, state)
    summary = ", ".join(f"{count} {state}" for state, count in sorted(counts.items()))
    logger.info("%d spec IDs: %s.", len(coverage.spec_ids), summary or "none")
    return EXIT_OK


def check_milestone(coverage: Coverage, milestone_id: int, block: list[str]) -> int:
    """Log the state of each spec ID in the block's Refs; fail when one is not tested or manual."""
    ids = refs_ids(block)
    failed = []
    for spec_id in ids:
        state = coverage.state(spec_id)
        logger.info("%-7s %s", spec_id, state)
        if state not in COVERED_STATES:
            failed.append(spec_id)
    if failed:
        logger.error(
            "M%d: no test and no Manual entry for %s.", milestone_id, ", ".join(failed)
        )
        return EXIT_NOT_COVERED
    logger.info("M%d: %d spec ID(s) in Refs, all tested or manual.", milestone_id, len(ids))
    return EXIT_OK


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Read the command line: an optional milestone (M<n>) and an optional root folder."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "milestone", nargs="?", help="check only the Refs of this milestone, for example M3"
    )
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="the folder that holds docs/ and tests/"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """List every spec ID, or check one milestone. Return the exit code."""
    arguments = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    root = arguments.root.resolve()
    if not (root / SPEC_PATH).is_file():
        logger.error("%s is missing in %s.", SPEC_PATH.as_posix(), root)
        return EXIT_USAGE
    plan_lines = read_lines(root / PLAN_PATH)
    blocks = milestone_blocks(plan_lines)
    coverage = read_coverage(root, blocks, plan_lines)
    if arguments.milestone is None:
        return list_all(coverage)
    match = MILESTONE_ARGUMENT.fullmatch(arguments.milestone)
    if match is None or int(match[1]) not in blocks:
        logger.error("No block '### %s' in %s.", arguments.milestone, PLAN_PATH.as_posix())
        return EXIT_USAGE
    return check_milestone(coverage, int(match[1]), blocks[int(match[1])])


if __name__ == "__main__":
    sys.exit(main())
