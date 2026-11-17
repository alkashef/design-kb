"""The threshold service: reads, saves and resets the level thresholds (FR-31, FR-32, FR-35, FR-36)."""

import logging
from typing import List, Optional

from src.domain import entry_rules, levels
from src.domain.models import Threshold

logger = logging.getLogger(__name__)

THRESHOLD_LEVELS = (2, 3, 4)


class ThresholdError(Exception):
    """Raised when an entry is rejected; the message is shown to the user."""


def _whole_number(text: str, label: str) -> int:
    """Return text as a whole number of 0 or more, or raise ThresholdError."""
    clean = text.strip()
    if not (clean.isascii() and clean.isdigit()):
        raise ThresholdError(f"{label} must be a whole number of 0 or more.")
    return int(clean)


def _optional_number(text: str, label: str) -> Optional[int]:
    """Return None for an empty text (no upper limit), else the whole number."""
    return None if not text.strip() else _whole_number(text, label)


class ThresholdService:
    """Reads and changes the thresholds through the store."""

    def __init__(self, store):
        """Use store (a LanceStore or a fake)."""
        self._store = store

    def current(self) -> List[Threshold]:
        """Return the saved thresholds, or the defaults when none are saved (FR-32)."""
        return self._store.list_thresholds() or levels.default_thresholds()

    def save(self, fields: dict) -> None:
        """Save the thresholds from the 12 form fields, or raise ThresholdError with the message."""
        thresholds = [self._parse_level(n, fields) for n in THRESHOLD_LEVELS]
        problem = entry_rules.threshold_problem(thresholds)
        if problem:
            raise ThresholdError(problem)
        self._store.replace_thresholds(thresholds)
        logger.info("Saved the thresholds.")

    def reset(self) -> None:
        """Restore the default thresholds (FR-36)."""
        self._store.replace_thresholds([])
        logger.info("Reset the thresholds.")

    @staticmethod
    def _parse_level(level: int, fields: dict) -> Threshold:
        """Return the Threshold of one level from its 4 form fields."""
        prefix = f"level{level}_"
        name = f"Level {level}"
        return Threshold(
            level=level,
            lead_from=_whole_number(fields.get(prefix + "lead_from", ""), f"{name} lead from"),
            lead_to=_optional_number(fields.get(prefix + "lead_to", ""), f"{name} lead to"),
            member_from=_whole_number(fields.get(prefix + "member_from", ""), f"{name} member from"),
            member_to=_optional_number(fields.get(prefix + "member_to", ""), f"{name} member to"),
        )
