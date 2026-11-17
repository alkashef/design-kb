"""Run the milestones of docs/plan.md one after another, each in two unattended claude sessions.

Each milestone of the table "Milestones at a glance" runs in two fresh `claude -p` sessions with
the model and effort its row names, following the loop of docs/workflow.md (Execute). First the
runner reads the milestone's block from the plan. The test session runs /write-tests: it writes
the milestone's tests and may not read the code in src/. The runner then writes the SHA-256 of
every file under tests/ (not __pycache__), with that block, to .claude/logs/M<n>-tests.json. The
build session makes the tests pass and may not edit tests/. After it, the runner compares the
hashes and runs `python scripts/spec_coverage.py M<n>` over a temporary copy of docs/specs.md and
tests/ with the block it read first (the build session deletes the block from the plan). A test
file that changed, was added or was removed, or a failed coverage check, means the milestone did
not finish.

Before the first milestone, the runner checks the conda environment, the settings file, the commit
hook, a clean git tree, an upstream branch and .gitignore. After each one, it checks that the
milestone's row left the plan, that git is clean and that everything was pushed. It stops at a row
whose Status is `blocked` and at a milestone that either session blocks, printing the milestone's
block with its question; the user adds an Approval entry, sets the Status to `approved`, commits,
and runs again. A session that did not finish is tried again (--retries, default 1) in a new
session that resumes from the changes the first one left; a retry repeats only that session. A
session that runs over --timeout-minutes counts as not finished. If the last try also fails, the
run stops, and --resume starts the next run from the changes left on a dirty tree: when the hashes
file of the milestone exists, its test session finished, so only the build session runs. It shows
a live status line, logs each session to .claude/logs/M<n>-test.log and M<n>.log (with -<try> for
a retry), appends a timing to .claude/logs/timings.csv, prints the DECISION lines of each report,
and ends with a summary table.

Does NOT edit the plan, the code or git: the claude sessions do that. The git pre-commit hook
still runs the tests on each milestone's commit. Each session starts with permission prompts off,
so its guard rails are the rules in .claude/settings.json, plus the --disallowedTools of its kind:
the runner refuses to start without that file.

Run, after `conda activate design-kb`:
    python scripts/milestones-runner.py [--start N] [--end N] [--retries N] [--resume]
        [--timeout-minutes N]
"""
import argparse
import csv
import ctypes
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import TracebackType
from typing import Final, NoReturn, Self

# The rules of a run (docs/workflow.md).
ENV_NAME: Final = "design-kb"
SPEC_FILE: Final = "specs.md"  # the name of the spec in docs/
VALID_MODELS: Final = ("haiku", "sonnet", "opus")  # aliases: the latest model of the family
MODEL_ID: Final = re.compile(r"claude-(haiku|sonnet|opus)-\d[a-z0-9-]*")  # a pinned version
VALID_EFFORTS: Final = ("low", "medium", "high", "xhigh", "max")
RESUME_NOTE: Final = (
    "A previous session worked on this milestone and did not finish. Its changes may still be in "
    "the working tree, and its commit may not be pushed. First run git status, git diff and "
    "git log @{u}..HEAD, then continue from there. Do not redo finished work. If the block already "
    "has a Blocked entry, only finish stopping it, as in rule (f)."
)
TEST_RESUME_NOTE: Final = (
    "A previous test session worked on this milestone and did not finish. Its test files may "
    "still be in tests/. First run git status and read them, then continue from there. Do not "
    "redo finished work."
)
SESSION_TEST: Final = "test"  # the session that writes the milestone's tests
SESSION_BUILD: Final = "build"  # the session that makes them pass
SRC_CODE: Final = ("py", "js", "html", "css")  # the code in src/ that a test session may not read
TEST_SESSION_DENIED: Final = tuple(
    f"{tool}(./src/**/*.{extension})" for tool in ("Read", "Grep", "Glob") for extension in SRC_CODE
)
BUILD_SESSION_DENIED: Final = ("Edit(./tests/**)", "Write(./tests/**)")
SKIPPED_DIR: Final = "__pycache__"
IGNORE_ENTRIES: Final = (".claude/logs/",)
HOOKS_PATH: Final = ".githooks"  # the value of git's core.hooksPath that turns the commit hook on
TAIL_LINES: Final = 30
DEFAULT_RETRIES: Final = 1  # extra tries of a milestone whose session did not finish
DEFAULT_TIMEOUT_MINUTES: Final = 90  # the longest one claude session may run
REFRESH_SECONDS: Final = 1.0
TIMEOUT_EXIT_CODE: Final = 124  # the exit code of a session the runner cut off (as GNU timeout)
OUTCOME_DONE: Final = "done"
OUTCOME_FAILED: Final = "failed"
OUTCOME_BLOCKED: Final = "blocked"
STATUS_BLOCKED: Final = "blocked"  # in the Status column: the milestone waits for an approval


@dataclass(frozen=True)
class BarStyle:
    """How a progress bar looks: its width in characters and its filled and empty characters."""

    width: int
    fill: str
    empty: str


# The live status line keeps within 79 columns, so an 80-column console does not wrap it.
LIVE_BAR: Final = BarStyle(10, "█", "░")
RANGE_BAR: Final = BarStyle(40, "|", "_")


@dataclass(frozen=True)
class Row:
    """One row of the table "Milestones at a glance" (model, effort and status in lower case)."""

    id: int
    title: str
    model: str
    effort: str
    status: str


@dataclass(frozen=True)
class Result:
    """How one milestone of this run ended (outcome: done, failed or blocked)."""

    id: int
    title: str
    model: str
    effort: str
    started_at: str
    seconds: float
    outcome: str


@dataclass(frozen=True)
class Progress:
    """Everything the live status line shows, at one moment."""

    done: int
    total: int
    row_id: int
    model: str
    effort: str
    milestone_seconds: float
    total_seconds: float
    finished_seconds: tuple[float, ...]


@dataclass(frozen=True)
class Options:
    """The command-line arguments. A start or end of None means the whole table."""

    start: int | None
    end: int | None
    retries: int
    resume: bool
    timeout_minutes: int


@dataclass(frozen=True)
class Attempt:
    """One try at a milestone: its number from 1, whether it resumes work, its time limit."""

    number: int
    resume: bool
    timeout_seconds: float


@dataclass(frozen=True)
class Paths:
    """The files the runner reads and writes, below the repository root."""

    root: Path

    @property
    def plan(self) -> Path:
        """docs/plan.md."""
        return self.root / "docs" / "plan.md"

    @property
    def log_dir(self) -> Path:
        """.claude/logs, with one log per milestone."""
        return self.root / ".claude" / "logs"

    @property
    def gitignore(self) -> Path:
        """.gitignore."""
        return self.root / ".gitignore"

    @property
    def settings(self) -> Path:
        """.claude/settings.json, the rules that guard an unattended session."""
        return self.root / ".claude" / "settings.json"

    @property
    def timings(self) -> Path:
        """.claude/logs/timings.csv."""
        return self.log_dir / "timings.csv"

    def tests_file(self, milestone_id: int) -> Path:
        """.claude/logs/M<n>-tests.json: the hashes of tests/ after the test session."""
        return self.log_dir / f"M{milestone_id}-tests.json"


@dataclass(frozen=True)
class ClaudeRun:
    """The output lines and the exit code of one `claude -p` run; timed_out if it was cut off."""

    lines: list[str]
    exit_code: int
    timed_out: bool = False
    log_name: str = ""


@dataclass(frozen=True)
class SavedTests:
    """What the runner keeps after a test session: the milestone's block, the hashes of tests/."""

    block: list[str]
    hashes: dict[str, str]


@dataclass(frozen=True)
class Verdict:
    """The judgement of a finished run: its outcome and, for a failure, the reason."""

    outcome: str
    reason: str


class RunStoppedError(Exception):
    """The run must stop. main() prints the message and the detail lines, then the summary."""

    def __init__(self, message: str, details: Sequence[str] = (), color: str = "red") -> None:
        """Keep the first line, the lines under it, and the color of the first line."""
        super().__init__(message)
        self.message = message
        self.details = tuple(details)
        self.color = color


class Stopwatch:
    """Counts the seconds since it was made."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Start counting now. A test passes its own clock."""
        self._clock = clock
        self._start = clock()

    def elapsed(self) -> float:
        """Return the seconds counted so far."""
        return self._clock() - self._start


@dataclass
class RunState:
    """What this run has done so far: the milestones to run, the total timer and the results.

    resume_next is True until the first milestone starts, when --resume was given.
    """

    total: int
    stopwatch: Stopwatch
    results: list[Result] = field(default_factory=list)
    resume_next: bool = False

    def take_resume(self) -> bool:
        """Return whether the milestone that starts now resumes work; only the first one does."""
        resume, self.resume_next = self.resume_next, False
        return resume

    def progress(self, row: Row, milestone: Stopwatch) -> Progress:
        """Return the numbers for the live status line while `row` runs."""
        return Progress(
            done=len(self.results),
            total=self.total,
            row_id=row.id,
            model=row.model,
            effort=row.effort,
            milestone_seconds=milestone.elapsed(),
            total_seconds=self.stopwatch.elapsed(),
            finished_seconds=tuple(result.seconds for result in self.results),
        )


@dataclass(frozen=True)
class Console:
    """Prints to the terminal: ANSI colors when use_color is True, plain text when it is False."""

    use_color: bool

    def paint(self, text: str, color: str) -> str:
        """Return the text in "green", "yellow" or "red"; unchanged when colors are off."""
        if not self.use_color:
            return text
        code = {"green": "32", "yellow": "33", "red": "31"}[color]
        return f"\x1b[{code}m{text}\x1b[0m"

    def say(self, text: str = "", color: str | None = None) -> None:
        """Print one permanent line."""
        print(text if color is None else self.paint(text, color), flush=True)

    def overwrite(self, text: str, color: str) -> None:
        """Replace the current terminal line with the text, cut to the width of the terminal."""
        width = shutil.get_terminal_size().columns - 1
        sys.stdout.write(self._erase(width) + self.paint(text[:width], color))
        sys.stdout.flush()

    def clear_line(self) -> None:
        """Erase the current terminal line and put the cursor at its start."""
        sys.stdout.write(self._erase(shutil.get_terminal_size().columns - 1))
        sys.stdout.flush()

    def _erase(self, width: int) -> str:
        """Return the characters that clear the current line."""
        if self.use_color:
            return "\r\x1b[2K"
        return "\r" + " " * width + "\r"


PLAIN_CONSOLE: Final = Console(use_color=False)


@dataclass(frozen=True)
class Session:
    """Everything one run needs: the files, the terminal, the state and the range."""

    paths: Paths
    console: Console
    state: RunState
    first: int
    last: int
    options: Options


class LiveStatus:
    """Redraws one status line every second from a thread. Use it in a `with` block."""

    def __init__(self, console: Console, render: Callable[[], str]) -> None:
        """Keep the console and the function that returns the text of the line."""
        self._console = console
        self._render = render
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def __enter__(self) -> Self:
        """Start the thread."""
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the thread, also after an error, and erase the line."""
        self._stop.set()
        self._thread.join()
        self._console.clear_line()

    def _loop(self) -> None:
        """Draw, then wait one second or until stop; repeat."""
        while True:
            self._console.overwrite(self._render(), "yellow")
            if self._stop.wait(REFRESH_SECONDS):
                return


# --- reading the plan ----------------------------------------------------------------------------


def _split_lines(text: str) -> list[str]:
    """Split on CRLF, LF or CR only (str.splitlines also splits on form feeds and more)."""
    return re.split(r"\r\n|\r|\n", text)


def _read_lines(path: Path) -> list[str]:
    """Return the lines of a UTF-8 file (a byte order mark is dropped)."""
    return _split_lines(path.read_text(encoding="utf-8-sig"))


def parse_row(line: str) -> Row | None:
    """Read one table row: | **M<n>** Title | Description | Model | Effort | Status |.

    Args:
        line: One line of the plan.

    Returns:
        The row, or None when the line is not a milestone row.
    """
    match = re.match(
        r"^\|\s*\*\*M(?P<id>\d+)\*\*\s*(?P<title>[^|]*?)\s*\|\s*(?P<text>.*)\|\s*(?P<model>[^|]*?)\s*"
        r"\|\s*(?P<effort>[^|]*?)\s*\|\s*(?P<status>[^|]*?)\s*\|\s*$",
        line,
        re.IGNORECASE,
    )
    if match is None:
        return None
    return Row(
        id=int(match["id"]),
        title=match["title"].replace("**", "").strip(),
        model=match["model"].strip().lower(),
        effort=match["effort"].strip().lower(),
        status=match["status"].strip().lower(),
    )


def parse_plan_rows(lines: Sequence[str]) -> list[Row]:
    """Return the rows of the table "Milestones at a glance", in the order of the file.

    Args:
        lines: The lines of docs/plan.md.

    Returns:
        The rows between that heading and the next heading of level 1 to 3.
    """
    rows: list[Row] = []
    in_table = False
    for line in lines:
        if re.match(r"^## Milestones at a glance", line, re.IGNORECASE):
            in_table = True
        elif in_table and re.match(r"^#{1,3} ", line):
            break
        elif in_table:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    return rows


def plan_has_row(lines: Sequence[str], milestone_id: int) -> bool:
    """Tell whether the table "Milestones at a glance" still has a row for the milestone.

    A finished milestone leaves the table: its commit deletes its block and its row
    (docs/workflow.md).

    Args:
        lines: The lines of docs/plan.md.
        milestone_id: The milestone number.

    Returns:
        True when the table has the row of that milestone.
    """
    return any(row.id == milestone_id for row in parse_plan_rows(lines))


def plan_row(lines: Sequence[str], milestone_id: int) -> Row | None:
    """Return the milestone's row of the table "Milestones at a glance", or None if it left."""
    return next((row for row in parse_plan_rows(lines) if row.id == milestone_id), None)


def milestone_block(lines: Sequence[str], milestone_id: int) -> list[str]:
    """Return the lines of the milestone's `### M<n>` block, up to the next heading."""
    block: list[str] = []
    inside = False
    for line in lines:
        if re.match(r"^#{1,3} ", line):
            inside = re.match(rf"^### M{milestone_id}\b", line) is not None
        if inside:
            block.append(line)
    return block



def rows_in_range(rows: Sequence[Row], first: int, last: int) -> list[Row]:
    """Return the rows numbered first to last, in table order (not numeric order)."""
    return [row for row in rows if first <= row.id <= last]


def next_open_row(rows: Sequence[Row]) -> Row | None:
    """Return the first row, in table order, whose status is not "done"."""
    return next((row for row in rows if row.status != "done"), None)


def resolve_range(rows: Sequence[Row], start: int | None, end: int | None) -> tuple[int, int]:
    """Return the first and last milestone number; a missing start or end means the whole table."""
    ids = [row.id for row in rows]
    return (
        min(ids, default=0) if start is None else start,
        max(ids, default=0) if end is None else end,
    )


def range_problem(first: int, last: int) -> str | None:
    """Return why the range is refused (a start after the end), or None."""
    if first > last:
        return f"--start ({first}) is greater than --end ({last})."
    return None


def row_problem(row: Row) -> str | None:
    """Return why the model or effort of the row cannot be used, or None."""
    if not row.model or not row.effort:
        return f"M{row.id} has no Model or no Effort in the table."
    if row.model not in VALID_MODELS and not MODEL_ID.fullmatch(row.model):
        return (
            f"M{row.id}: Model '{row.model}' is not one of {', '.join(VALID_MODELS)} "
            "or a full model ID such as claude-sonnet-5-5."
        )
    if row.effort not in VALID_EFFORTS:
        return f"M{row.id}: Effort '{row.effort}' is not one of {', '.join(VALID_EFFORTS)}."
    return None


def build_prompt(row: Row, resume: bool) -> str:
    """Return the text sent to claude for one milestone; resume adds the note for a retry."""
    resume_note = (RESUME_NOTE,) if resume else ()
    text = " ".join(
        (
            "Implement only milestone M<n> (<title>) from docs/plan.md.",
            "Follow its block, the loop in docs/workflow.md (steps 4 to 6) and CLAUDE.md.",
            "This is the build session: a test session has already written the milestone's tests.",
            "Make them pass, and change no file in tests/.",
            "This is an unattended run: nobody can answer questions.",
            *resume_note,
            "Rules:",
            "(a) never edit docs/specs.md: a settings rule denies that edit in an unattended run;",
            "(b) in docs/plan.md, when the gate passes, delete the block of M<n> and its row in",
            'the table "Milestones at a glance", and edit nothing else in the plan;',
            "(c) do that edit before the commit so the commit includes it;",
            "(d) commit only the files this milestone changed, with the message `M<n>: <title>`,",
            "then run git push;",
            "(e) if the pre-commit hook refuses the commit, fix the cause; never bypass the hook;",
            "(f) stop the milestone only if it needs a new or changed requirement in",
            "docs/specs.md, an action that CLAUDE.md 'Git and destructive actions' forbids, a new",
            "flow of user data to an external service, real user data, a secret in a committed",
            "file, a library that docs/design.md does not name in a Decided decision (use the",
            "standard library first), or a change to a test in tests/ that you find wrong, and no",
            "Approval entry in the block permits it. To stop: set",
            "its Status in the table to `blocked`, add a Blocked entry with the reason and the",
            "exact question to its block (template in docs/workflow.md), commit docs/plan.md",
            "alone with the message `M<n>: blocked`, and run git push. Before that commit, undo",
            "your other changes with Edit and by deleting the files you added (git restore",
            "and git clean are denied), so git status lists only docs/plan.md;",
            "(g) an Approval entry in the block is the user's decision: it permits exactly what it",
            "says, even an action these rules or CLAUDE.md otherwise forbid, and nothing more;",
            "(h) a tool call that a settings rule denies is not allowed in an unattended run: do",
            "not retry it or work around it. Choose another way, or stop as in (f) if none;",
            "(i) for anything else that is open, such as a gap in docs/design.md or a detail of a",
            "library, decide the most conservative option and carry on. If docs/specs.md and",
            "docs/design.md disagree, the spec wins: fix the design. When the decision changes the",
            "design, add a D-NN (the next free number) to docs/design.md with the Status Proposed,",
            "and write 'auto-decided in M<n>, review' in its Reason. Never renumber an ID;",
            "(j) never call the embedding model in Ollama, and do not start the app for a person;",
            "a test may start its own server on 127.0.0.1 with the fake embedding client. The",
            "Gate is `python scripts/check.py`, whose tests run with the fake embedding client, in",
            "temporary folders, and `python scripts/spec_coverage.py M<n>`. A check that needs the",
            "live embedding model or a person is a human check of docs/plan.md, not yours;",
            "(k) end with the report in CLAUDE.md 'Communication and reporting'. In it, write each",
            "decision of (i) as its own line: `DECISION: <what> | <why> | <D-NN or none>`.",
        )
    )
    return text.replace("<n>", str(row.id)).replace("<title>", row.title)


def build_test_prompt(row: Row, resume: bool = False) -> str:
    """Return the text sent to the test session of a milestone; resume adds the note for a retry."""
    resume_note = (TEST_RESUME_NOTE,) if resume else ()
    text = " ".join(
        (
            "Run /write-tests for milestone M<n> (<title>) of docs/plan.md.",
            "This is the test session (docs/workflow.md, Execute); a build session",
            "writes the code afterwards and may not change your tests.",
            "This is an unattended run: nobody can answer questions.",
            *resume_note,
            "Rules:",
            "(a) commit nothing; the only exception is the commit that blocks the milestone (d);",
            "(b) change only files under tests/, docs/design.md for an auto-decision (c), and",
            "docs/plan.md only to block the milestone (d). Never edit docs/specs.md, and never",
            "read the code in src/ (*.py, *.js, *.html, *.css), also not through the shell;",
            "(c) for a gap in docs/design.md or a detail of a library, decide the most",
            "conservative option and carry on. When the decision changes the design, add a D-NN",
            "(the next free number) to docs/design.md with the Status Proposed, and write",
            "'auto-decided in M<n>, review' in its Reason. Never renumber an ID;",
            "(d) stop the milestone only if its tests need a new or changed requirement in",
            "docs/specs.md, an action that CLAUDE.md 'Git and destructive actions' forbids, real",
            "user data, or a library that docs/design.md does not name in a Decided decision, and",
            "no Approval entry in the block permits it. To stop: delete the files you added and",
            "undo your other changes, set its Status in the table to `blocked`, add a Blocked",
            "entry with the reason and the exact question to its block (template in",
            "docs/workflow.md),",
            "commit docs/plan.md alone with the message `M<n>: blocked`, and run git push;",
            "(e) a tool call that a settings rule denies is not allowed: do not retry it or work",
            "around it;",
            "(f) never call the embedding model in Ollama and do not start the app; a test may",
            "start its own server on 127.0.0.1 with the fake embedding client;",
            "(g) end with the report of /write-tests. In it, write each decision of (c) as its own",
            "line: `DECISION: <what> | <why> | <D-NN or none>`.",
        )
    )
    return text.replace("<n>", str(row.id)).replace("<title>", row.title)


def session_command(row: Row, kind: str) -> list[str]:
    """Return the claude command of one session of a milestone, with the tools its kind denies.

    Args:
        row: The milestone; its model and effort go to claude.
        kind: SESSION_TEST (may not read the code in src/) or SESSION_BUILD (may not edit tests/).

    Returns:
        The command; --disallowedTools comes last, because it takes every argument after it.
    """
    denied = TEST_SESSION_DENIED if kind == SESSION_TEST else BUILD_SESSION_DENIED
    program = shutil.which("claude") or "claude"
    return [
        program,
        "-p",
        "--model",
        row.model,
        "--effort",
        row.effort,
        "--permission-mode",
        "bypassPermissions",
        "--disallowedTools",
        *denied,
    ]


# --- the tests a test session wrote --------------------------------------------------------------


def snapshot_tests(root: Path) -> dict[str, str]:
    """Return the SHA-256 of every file under root/tests, keyed by its path from root.

    Args:
        root: The repository root (the folder that holds tests/).

    Returns:
        Path (with / separators) to hex digest, sorted by path; files in __pycache__ are skipped.
    """
    hashes = {}
    for path in sorted((root / "tests").rglob("*")):
        relative = path.relative_to(root)
        if path.is_file() and SKIPPED_DIR not in relative.parts:
            hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def changed_tests(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return the paths whose hash changed, that were added, or that were removed, sorted."""
    paths = before.keys() | after.keys()
    return sorted(path for path in paths if before.get(path) != after.get(path))


def save_tests(path: Path, saved: SavedTests) -> None:
    """Write the milestone's block and the hashes to the milestone's hashes file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"block": saved.block, "hashes": saved.hashes}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_tests(path: Path) -> SavedTests | None:
    """Return what a finished test session left in the hashes file, or None if there is none."""
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return SavedTests(block=data["block"], hashes=data["hashes"])


def coverage_problem(root: Path, milestone_id: int, block: Sequence[str]) -> str | None:
    """Run `python scripts/spec_coverage.py M<n>` with the block read before the test session.

    The build session deletes the block from the plan, so the script reads a temporary tree: a
    copy of docs/specs.md and tests/, and a plan that holds only that block. The script reads the
    spec IDs of its Refs and the `Manual:` parts of its Tests first.

    Returns:
        Why the check failed, with its output, or None when it passed.
    """
    with tempfile.TemporaryDirectory() as folder:
        copy = Path(folder)
        (copy / "docs").mkdir()
        shutil.copyfile(root / "docs" / SPEC_FILE, copy / "docs" / SPEC_FILE)
        shutil.copytree(root / "tests", copy / "tests", ignore=shutil.ignore_patterns(SKIPPED_DIR))
        (copy / "docs" / "plan.md").write_text("\n".join(block) + "\n", encoding="utf-8")
        script = root / "scripts" / "spec_coverage.py"
        done = _run([sys.executable, str(script), f"M{milestone_id}", "--root", folder], root)
    if done.returncode == 0:
        return None
    return f"python scripts/spec_coverage.py M{milestone_id} failed:\n{done.stdout.strip()}"


def tests_problem(paths: Paths, row: Row, saved: SavedTests) -> str | None:
    """Return why a finished build session does not count: tests/ changed, or coverage failed."""
    changed = changed_tests(saved.hashes, snapshot_tests(paths.root))
    if changed:
        return f"the build session changed files in tests/: {', '.join(changed)}."
    return coverage_problem(paths.root, row.id, saved.block)


# --- arguments, environment and git --------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> Options:
    """Read the command line.

    Args:
        argv: The arguments; None means sys.argv.

    Returns:
        The options. Without --start and --end the whole table is run.
    """
    parser = argparse.ArgumentParser(
        description="Run the milestones of docs/plan.md, one claude session each."
    )
    parser.add_argument(
        "--start", type=int, default=None, help="first milestone number (default: the first row)"
    )
    parser.add_argument(
        "--end", type=int, default=None, help="last milestone number (default: the last row)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"extra tries of a milestone that did not finish (default: {DEFAULT_RETRIES})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="start on a dirty git tree: the first milestone continues the changes it left",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=int,
        default=DEFAULT_TIMEOUT_MINUTES,
        help=f"longest time of one claude session (default: {DEFAULT_TIMEOUT_MINUTES})",
    )
    args = parser.parse_args(argv)
    if args.retries < 0:
        parser.error("--retries must be 0 or more.")
    if args.timeout_minutes < 1:
        parser.error("--timeout-minutes must be 1 or more.")
    return Options(
        start=args.start,
        end=args.end,
        retries=args.retries,
        resume=args.resume,
        timeout_minutes=args.timeout_minutes,
    )


def in_project_env(prefix: str) -> bool:
    """Tell whether a Python prefix (sys.prefix) is the project's conda environment."""
    return Path(prefix).name.lower() == ENV_NAME.lower()


def missing_ignore_entries(existing: Sequence[str]) -> list[str]:
    """Return the entries of IGNORE_ENTRIES that are not a line of .gitignore (case-insensitive)."""
    known = {line.lower() for line in existing}
    return [entry for entry in IGNORE_ENTRIES if entry.lower() not in known]


def add_ignore_entries(gitignore: Path) -> bool:
    """Append the missing entries to .gitignore.

    Args:
        gitignore: The path of .gitignore.

    Returns:
        True when it had to add a line.
    """
    text = gitignore.read_text(encoding="utf-8-sig") if gitignore.exists() else ""
    missing = missing_ignore_entries(_split_lines(text))
    if not missing:
        return False
    # Start on a new line, so the first entry does not join a last line without a line end.
    start = "\n" if text and not text.endswith(("\n", "\r")) else ""
    with gitignore.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(start + "\n".join(missing) + "\n")
    return True


def _run(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a command in the repository and return its result, or stop the run if it cannot start."""
    try:
        return subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise _error(f"`{args[0]}` could not run: {exc}") from exc


def git_is_clean(root: Path) -> bool:
    """Tell whether `git status --porcelain` succeeds and lists nothing."""
    done = _run(["git", "status", "--porcelain"], root)
    return done.returncode == 0 and not done.stdout.strip()


def git_has_upstream(root: Path) -> bool:
    """Tell whether the current branch has an upstream, so that git push works."""
    done = _run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root)
    return done.returncode == 0


def git_hook_is_on(root: Path) -> bool:
    """Tell whether git runs this project's pre-commit hook (core.hooksPath is .githooks)."""
    done = _run(["git", "config", "--get", "core.hooksPath"], root)
    return done.returncode == 0 and done.stdout.strip().rstrip("/") == HOOKS_PATH


def git_has_unpushed(root: Path) -> bool:
    """Tell whether HEAD has commits that are not on the upstream (True when git cannot tell)."""
    done = _run(["git", "rev-list", "--count", "@{u}..HEAD"], root)
    return done.returncode != 0 or int(done.stdout.strip() or "0") > 0


def _error(message: str) -> RunStoppedError:
    """Build the stop for a plain error: "ERROR: <message>" in red."""
    return RunStoppedError(f"ERROR: {message}")


def check_range(first: int, last: int) -> None:
    """Refuse a range whose start is after its end.

    Args:
        first: The first milestone number.
        last: The last milestone number.

    Raises:
        RunStoppedError: If the range is refused.
    """
    problem = range_problem(first, last)
    if problem is not None:
        raise _error(problem)


def preflight(paths: Paths, allow_dirty: bool) -> None:
    """Check the environment before the first milestone; allow_dirty (--resume) skips the git check.

    Args:
        paths: The repository files.
        allow_dirty: True when the first milestone may start on a tree with uncommitted changes.

    Raises:
        RunStoppedError: If the conda env is wrong, the settings file is missing, the commit hook
            is off, git is not clean (unless allow_dirty), the branch has no upstream, or
            .gitignore had to be changed.
    """
    if not in_project_env(sys.prefix):
        raise _error(
            f"Python runs from '{sys.prefix}', not from the conda env '{ENV_NAME}'. "
            f"Run 'conda activate {ENV_NAME}' first."
        )
    if not paths.settings.is_file():
        raise _error(
            ".claude/settings.json is missing. Its rules guard a session that runs with "
            "permission prompts off (docs/workflow.md), so the run does not start without it."
        )
    if not git_hook_is_on(paths.root):
        raise _error(
            "The pre-commit hook is off, so a commit would not run the tests. "
            f"Turn it on with: git config core.hooksPath {HOOKS_PATH}"
        )
    if not allow_dirty and not git_is_clean(paths.root):
        raise _error(
            "git status is not clean. Commit or stash your changes first, "
            "or run with --resume to continue the changes a failed milestone left."
        )
    if not git_has_upstream(paths.root):
        raise _error(
            "The current branch has no upstream, so git push cannot work. "
            "Set one with: git push -u origin <branch>"
        )
    if add_ignore_entries(paths.gitignore):
        raise _error(
            f".gitignore was missing {', '.join(IGNORE_ENTRIES)}; the lines are added now. "
            "Commit .gitignore, then run again."
        )


# --- time and display ----------------------------------------------------------------------------


def format_duration(seconds: float) -> str:
    """Return mm:ss, or h:mm:ss from one hour on (the seconds are cut, not rounded)."""
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def bar_text(done: int, total: int, style: BarStyle) -> str:
    """Return a bar of `style.width` characters, filled by the share done/total (rounded down)."""
    filled = min(style.width * done // total, style.width) if total > 0 else 0
    return style.fill * filled + style.empty * (style.width - filled)


def percent(done: int, total: int) -> int:
    """Return 100 * done / total, rounded (0 when total is 0)."""
    return round(100 * done / total) if total > 0 else 0


def eta_text(finished_seconds: Sequence[float], left: int) -> str:
    """Return "ETA mm:ss": the average time of the finished milestones times the milestones left."""
    if not finished_seconds:
        return "ETA --"
    average = sum(finished_seconds) / len(finished_seconds)
    return f"ETA {format_duration(average * left)}"


def status_text(progress: Progress) -> str:
    """Return the live status line (without colors) for one moment of the run."""
    bar = bar_text(progress.done, progress.total, LIVE_BAR)
    return " | ".join(
        (
            f"{bar} {percent(progress.done, progress.total)}% {progress.done}/{progress.total}",
            f"M{progress.row_id} {progress.model.removeprefix('claude-')}/{progress.effort}",
            f"this {format_duration(progress.milestone_seconds)}",
            f"total {format_duration(progress.total_seconds)}",
            eta_text(progress.finished_seconds, progress.total - progress.done),
        )
    )


def outcome_color(outcome: str) -> str:
    """Return green for done, yellow for blocked and red for failed."""
    return {OUTCOME_DONE: "green", OUTCOME_BLOCKED: "yellow"}.get(outcome, "red")


def result_line(result: Result) -> str:
    """Return the permanent line of a finished milestone."""
    return " | ".join(
        (
            f"M{result.id} {result.title}",
            result.model,
            result.effort,
            format_duration(result.seconds),
            result.outcome,
        )
    )


def _table_lines(results: Sequence[Result], console: Console) -> list[str]:
    """Return the aligned table of this run's milestones, each row in the color of its outcome."""
    header = ("ID", "Model", "Effort", "Duration", "Result")
    cells = [
        (f"M{r.id}", r.model, r.effort, format_duration(r.seconds), r.outcome) for r in results
    ]
    widths = [max(len(cell) for cell in column) for column in zip(header, *cells, strict=True)]
    lines = [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in (header, *cells)
    ]
    return [lines[0]] + [
        console.paint(line, outcome_color(r.outcome))
        for line, r in zip(lines[1:], results, strict=True)
    ]


def summary_lines(
    results: Sequence[Result], total_seconds: float, console: Console = PLAIN_CONSOLE
) -> list[str]:
    """Return the summary of the run: a table, the total time, the average and the slowest one.

    Args:
        results: The milestones that ran, in order.
        total_seconds: The total time of the run.
        console: Paints the rows of the table (the default adds no colors).

    Returns:
        The lines to print; an empty list when no milestone ran.
    """
    if not results:
        return []
    slowest = max(results, key=lambda result: result.seconds)
    average = sum(result.seconds for result in results) / len(results)
    return [
        "Summary",
        *_table_lines(results, console),
        f"Total time: {format_duration(total_seconds)}",
        f"Average: {format_duration(average)}",
        f"Slowest: M{slowest.id} ({format_duration(slowest.seconds)})",
    ]


def print_summary(console: Console, state: RunState) -> None:
    """Print the summary of the run, if any milestone ran."""
    lines = summary_lines(state.results, state.stopwatch.elapsed(), console)
    if lines:
        console.say()
        for line in lines:
            console.say(line)


def enable_ansi() -> bool:
    """Turn on ANSI colors in the console.

    Returns:
        True when colors work; False when output is not a terminal or Windows refuses.
    """
    if not sys.stdout.isatty():
        return False
    if sys.platform != "win32":
        return True
    stdout_handle, virtual_terminal = -11, 0x0004
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(stdout_handle)
        mode = ctypes.c_ulong()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | virtual_terminal))
    except (AttributeError, OSError):
        return False


def start_console() -> Console:
    """Switch standard output to UTF-8 and return a Console with colors if they work."""
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    return Console(use_color=enable_ansi())


# --- running a milestone -------------------------------------------------------------------------


def _output_lines(text: str) -> list[str]:
    """Split the output of a run into lines, without the line ends at its end."""
    stripped = text.rstrip("\r\n")
    return _split_lines(stripped) if stripped else []


def _claude_process(command: Sequence[str], root: Path, prompt: str, timeout: float) -> ClaudeRun:
    """Run claude with the prompt on standard input; a run over `timeout` seconds is cut off."""
    try:
        done = subprocess.run(
            list(command),
            cwd=root,
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        # Not re-raised: running over the time limit is a verdict (failed), so it is retried.
        partial = (
            exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout
        )
        lines = [
            *_output_lines(partial or ""),
            f"[runner] claude was stopped after {timeout / 60:.0f} minutes.",
        ]
        return ClaudeRun(lines, TIMEOUT_EXIT_CODE, timed_out=True)
    except OSError as exc:
        raise _error(f"claude could not run: {exc}") from exc
    return ClaudeRun(_output_lines(done.stdout), done.returncode)


def log_file_name(row: Row, kind: str, number: int) -> str:
    """Return M<n>.log for a build session, M<n>-test.log for a test session; -<try> on a retry."""
    stem = f"M{row.id}" if kind == SESSION_BUILD else f"M{row.id}-{SESSION_TEST}"
    return f"{stem}.log" if number == 1 else f"{stem}-{number}.log"


def run_claude(paths: Paths, row: Row, attempt: Attempt, kind: str) -> ClaudeRun:
    """Run one try of one session of a milestone in `claude -p` and save its output to its log.

    Args:
        paths: The repository files.
        row: The milestone; its model and effort go to claude.
        attempt: Which try this is, whether it resumes earlier work, and its time limit.
        kind: SESSION_TEST or SESSION_BUILD.

    Returns:
        The output lines (standard output and error together), the exit code and the log name.

    Raises:
        RunStoppedError: If the claude program cannot be found or started.
    """
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    if kind == SESSION_TEST:
        prompt = build_test_prompt(row, attempt.resume)
    else:
        prompt = build_prompt(row, attempt.resume)
    command = session_command(row, kind)
    run = _claude_process(command, paths.root, prompt, attempt.timeout_seconds)
    log_name = log_file_name(row, kind, attempt.number)
    (paths.log_dir / log_name).write_text(
        "".join(f"{line}\n" for line in run.lines), encoding="utf-8"
    )
    return replace(run, log_name=log_name)


def failure_reason(paths: Paths, row: Row, run: ClaudeRun) -> str | None:
    """Return why a run that finished or blocked its milestone does not count, or None."""
    after = plan_row(_read_lines(paths.plan), row.id)
    if after is not None and after.status != STATUS_BLOCKED:
        cause = (
            "it ran over the time limit" if run.timed_out else f"claude exit code {run.exit_code}"
        )
        return (
            "its row is still in the plan table and not blocked, so the commit that finishes "
            f"it was not made ({cause})."
        )
    if not git_is_clean(paths.root):
        return "git status is not clean."
    if git_has_unpushed(paths.root):
        return "there are commits that were not pushed."
    return None


def judge(paths: Paths, row: Row, run: ClaudeRun) -> Verdict:
    """Return done (its row left the plan), blocked (its row says so) or failed (with why)."""
    reason = failure_reason(paths, row, run)
    if reason is not None:
        return Verdict(OUTCOME_FAILED, reason)
    if plan_has_row(_read_lines(paths.plan), row.id):
        return Verdict(OUTCOME_BLOCKED, "")
    return Verdict(OUTCOME_DONE, "")


def judge_test_session(paths: Paths, row: Row, run: ClaudeRun) -> Verdict:
    """Return blocked (as judge), failed (cut off or a claude error) or done for a test session.

    A finished test session leaves its tests uncommitted; only a blocked one must leave git clean.
    """
    after = plan_row(_read_lines(paths.plan), row.id)
    if after is not None and after.status == STATUS_BLOCKED:
        return judge(paths, row, run)
    if run.timed_out:
        return Verdict(OUTCOME_FAILED, "the test session ran over the time limit.")
    if run.exit_code != 0:
        return Verdict(OUTCOME_FAILED, f"the test session ended with exit code {run.exit_code}.")
    return Verdict(OUTCOME_DONE, "")


def waiting_for_approval(paths: Paths, row: Row) -> RunStoppedError:
    """Build the stop for a blocked milestone: what to do, then its block with the question."""
    message = (
        f"M{row.id} waits for your approval. In docs/plan.md, add an Approval entry to its "
        "block, set its Status to `approved`, commit, and run again:"
    )
    return RunStoppedError(message, milestone_block(_read_lines(paths.plan), row.id), "yellow")


def stop_for(paths: Paths, row: Row, verdict: Verdict, run: ClaudeRun) -> NoReturn:
    """Stop the run because the milestone did not finish.

    Raises:
        RunStoppedError: Always. It carries the blocked milestone's question, or the reason and
            the last lines of output.
    """
    if verdict.outcome == OUTCOME_BLOCKED:
        raise waiting_for_approval(paths, row)
    intro = f"Last {TAIL_LINES} lines of output (full log: .claude/logs/{run.log_name}):"
    hint = "To continue from the changes it left, run again with --resume."
    tail = [intro, *run.lines[-TAIL_LINES:], hint]
    raise RunStoppedError(f"M{row.id} stopped: {verdict.reason}", tail)


def append_timing(path: Path, result: Result) -> None:
    """Append a row (ID, model, effort, start, seconds, result) to the CSV; new: a header first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(["id", "model", "effort", "start", "seconds", "result"])
        writer.writerow(
            [
                f"M{result.id}",
                result.model,
                result.effort,
                result.started_at,
                f"{result.seconds:.1f}",
                result.outcome,
            ]
        )


def record_result(session: Session, result: Result) -> None:
    """Keep the result, add it to timings.csv (only a warning if that fails), and print its line."""
    session.state.results.append(result)
    try:
        append_timing(session.paths.timings, result)
    except OSError as exc:
        session.console.say(f"WARNING: could not write {session.paths.timings}: {exc}", "yellow")
    session.console.say(result_line(result), outcome_color(result.outcome))


def decision_lines(lines: Sequence[str]) -> list[str]:
    """Return the lines of a report that record an automatic decision (`DECISION: ...`)."""
    return [line.strip() for line in lines if re.match(r"^\W*DECISION:", line.strip())]


def show_range_progress(session: Session, row: Row, run: ClaudeRun) -> None:
    """Print a bar of the milestones done, then the TLDR line and DECISION lines of the report."""
    done, total = len(session.state.results), session.state.total
    bar = bar_text(done, total, RANGE_BAR)
    session.console.say(f"M{row.id}/M{session.last} [{bar}] {percent(done, total)}%", "green")
    tldr = next(
        (line for line in reversed(run.lines) if re.search("TLDR", line, re.IGNORECASE)), None
    )
    if tldr is not None:
        session.console.say(tldr)
    for line in decision_lines(run.lines):
        session.console.say(line, "yellow")


def prepare_milestone(paths: Paths, row: Row) -> None:
    """Check what the milestone needs before claude starts.

    Raises:
        RunStoppedError: If it waits for an approval, or its model or effort cannot be used.
    """
    if row.status == STATUS_BLOCKED:
        raise waiting_for_approval(paths, row)
    problem = row_problem(row)
    if problem is not None:
        raise _error(problem)


def run_attempts(
    session: Session, row: Row, watch: Stopwatch, kind: str, resume: bool
) -> tuple[ClaudeRun, Verdict]:
    """Run one session of the milestone, with the live status line, until it is done or blocked.

    A try that did not finish is repeated, as a resume, up to `--retries` times.
    """
    judge_run = judge_test_session if kind == SESSION_TEST else judge
    number = 1
    while True:
        attempt = Attempt(number, resume, session.options.timeout_minutes * 60)
        with LiveStatus(session.console, lambda: status_text(session.state.progress(row, watch))):
            run = run_claude(session.paths, row, attempt, kind)
        verdict = judge_run(session.paths, row, run)
        if verdict.outcome != OUTCOME_FAILED or number > session.options.retries:
            return run, verdict
        session.console.say(
            f"M{row.id} {kind} session, try {number}, did not finish: {verdict.reason}", "yellow"
        )
        number, resume = number + 1, True


def run_test_session(
    session: Session, row: Row, watch: Stopwatch, resume: bool
) -> tuple[ClaudeRun, Verdict]:
    """Read the milestone's block, run the test session, then save it with the hashes of tests/.

    The old hashes file is deleted first, so the file exists only after a test session finished.
    """
    paths = session.paths
    block = milestone_block(_read_lines(paths.plan), row.id)
    paths.tests_file(row.id).unlink(missing_ok=True)
    run, verdict = run_attempts(session, row, watch, SESSION_TEST, resume)
    if verdict.outcome == OUTCOME_DONE:
        save_tests(paths.tests_file(row.id), SavedTests(block, snapshot_tests(paths.root)))
        for line in decision_lines(run.lines):
            session.console.say(line, "yellow")
    return run, verdict


def run_sessions(
    session: Session, row: Row, watch: Stopwatch, resume: bool
) -> tuple[ClaudeRun, Verdict]:
    """Run the test session (skipped on a resume after it finished), then the build session.

    Returns:
        The last session's run, and its verdict; a build session that changed tests/ or whose
        spec-ID check fails counts as failed.
    """
    paths = session.paths
    saved = load_tests(paths.tests_file(row.id)) if resume else None
    build_resumes = saved is not None
    if saved is None:
        run, verdict = run_test_session(session, row, watch, resume)
        if verdict.outcome != OUTCOME_DONE:
            return run, verdict
        saved = load_tests(paths.tests_file(row.id))
    run, verdict = run_attempts(session, row, watch, SESSION_BUILD, build_resumes)
    if verdict.outcome == OUTCOME_DONE and saved is not None:
        problem = tests_problem(paths, row, saved)
        if problem is not None:
            verdict = Verdict(OUTCOME_FAILED, problem)
    return run, verdict


def run_milestone(session: Session, row: Row) -> None:
    """Run one milestone (its two sessions, with their retries), time it, and check it finished.

    Raises:
        RunStoppedError: If the milestone is blocked or did not finish.
    """
    session.console.say()
    session.console.say(f"Starting M{row.id} | {row.model} | {row.effort}")
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")
    watch = Stopwatch()
    run, verdict = run_sessions(session, row, watch, session.state.take_resume())
    seconds = watch.elapsed()
    record_result(
        session,
        Result(row.id, row.title, row.model, row.effort, started_at, seconds, verdict.outcome),
    )
    if verdict.outcome != OUTCOME_DONE:
        stop_for(session.paths, row, verdict, run)
    show_range_progress(session, row, run)


def _range_rows(session: Session) -> list[Row]:
    """Return the rows of the range as the plan has them now (a milestone edits its own status)."""
    rows = parse_plan_rows(_read_lines(session.paths.plan))
    return rows_in_range(rows, session.first, session.last)


def run_all(options: Options, console: Console, paths: Paths, state: RunState) -> None:
    """Run every milestone of the range whose status is not done, in table order.

    Args:
        options: The command-line options.
        console: The terminal.
        paths: The repository files.
        state: Filled in as milestones finish; main() prints the summary from it.

    Raises:
        RunStoppedError: At the first problem that a retry did not solve.
    """
    if not paths.plan.is_file():
        raise _error("docs/plan.md is missing. Write the plan with /write-plan first.")
    rows = parse_plan_rows(_read_lines(paths.plan))
    first, last = resolve_range(rows, options.start, options.end)
    check_range(first, last)
    preflight(paths, options.resume)
    state.total = sum(1 for row in rows_in_range(rows, first, last) if row.status != "done")
    state.resume_next = options.resume
    session = Session(paths, console, state, first, last, options)
    while True:
        row = next_open_row(_range_rows(session))
        if row is None:
            console.say(f"Range M{first} to M{last} is done.", "green")
            return
        prepare_milestone(paths, row)
        run_milestone(session, row)


def run_guarded(options: Options, console: Console, paths: Paths, state: RunState) -> int:
    """Run the range; print a stop or an interrupt instead of a traceback. Return the exit code."""
    try:
        run_all(options, console, paths, state)
    except RunStoppedError as stop:
        console.say(stop.message, stop.color)
        for line in stop.details:
            console.say(line)
        return 1
    except KeyboardInterrupt:
        console.say("Interrupted.", "yellow")
        return 130
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the milestones and print the summary, also when the run stops early.

    Args:
        argv: The command-line arguments; None means sys.argv.

    Returns:
        0 when the range is done, 1 when a milestone stopped the run, 130 after Ctrl+C.
    """
    options = parse_args(argv)
    console = start_console()
    paths = Paths(Path(__file__).resolve().parent.parent)
    state = RunState(total=0, stopwatch=Stopwatch())
    try:
        return run_guarded(options, console, paths, state)
    finally:
        print_summary(console, state)  # also after an unexpected error


if __name__ == "__main__":
    sys.exit(main())
