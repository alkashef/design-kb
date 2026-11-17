"""Remove caches and generated artifacts by name.

Removes Python and tool caches, compiled files, log files, and the generated
`log/` folder. It never deletes source, docs, config, data, or dependencies.
Run it with `--dry-run` first to see what it would remove.
"""

import argparse
import logging
import shutil
from pathlib import Path

logger = logging.getLogger("cleanup")

ROOT = Path(__file__).resolve().parent.parent

# Folders removed wherever they are found.
CACHE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".cache",
}
# Files removed wherever they are found.
CACHE_FILE_PATTERNS = ("*.pyc", "*.log")
# Generated folders removed only at the repo root.
GENERATED_ROOT_DIRS = {"log"}
# Folders never entered: dependencies, version control, and user-owned content.
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "docs",
    "config",
    "data",
}


def find_targets(root: Path) -> list[Path]:
    """Return every cache folder, cache file, and generated folder under root."""
    targets = []
    pending = [root]
    while pending:
        folder = pending.pop()
        for entry in sorted(folder.iterdir()):
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in CACHE_DIR_NAMES or (
                    folder == root and entry.name in GENERATED_ROOT_DIRS
                ):
                    targets.append(entry)
                elif entry.name not in SKIP_DIR_NAMES:
                    pending.append(entry)
            elif any(entry.match(pattern) for pattern in CACHE_FILE_PATTERNS):
                targets.append(entry)
    return targets


def remove(path: Path, root: Path) -> None:
    """Delete one file or folder, refusing anything outside root."""
    path.resolve().relative_to(root)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> None:
    """Parse the options, list the targets, and remove them unless --dry-run."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list what would be removed and remove nothing",
    )
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    targets = find_targets(ROOT)
    for path in targets:
        logger.info(
            "%s %s",
            "would remove" if arguments.dry_run else "remove",
            path.relative_to(ROOT),
        )
        if not arguments.dry_run:
            remove(path, ROOT)
    logger.info(
        "%d item(s) %s.",
        len(targets),
        "found" if arguments.dry_run else "removed",
    )


if __name__ == "__main__":
    main()
