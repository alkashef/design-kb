"""The level rules: the level of an engineer in a leaf (spec section 2.5, FR-25, FR-27, FR-32)."""

from typing import List, Optional

from src.domain.models import Threshold

LEVEL_NAMES = {1: "Aware", 2: "Hands-on", 3: "Lead", 4: "Senior lead", 5: "Expert"}


def default_thresholds() -> List[Threshold]:
    """Return the default thresholds of levels 2, 3 and 4."""
    return [
        Threshold(level=2, lead_from=0, lead_to=0, member_from=1, member_to=None),
        Threshold(level=3, lead_from=1, lead_to=2, member_from=0, member_to=None),
        Threshold(level=4, lead_from=3, lead_to=None, member_from=0, member_to=None),
    ]


def _in_range(count: int, low: int, high: Optional[int]) -> bool:
    """Tell whether count is in the range; a high of None has no upper limit."""
    return count >= low and (high is None or count <= high)


def computed_level(lead_count: int, member_count: int, thresholds: List[Threshold]) -> Optional[int]:
    """Return the highest level whose two ranges contain the counts, or None (FR-25)."""
    matching = [
        t.level
        for t in thresholds
        if _in_range(lead_count, t.lead_from, t.lead_to)
        and _in_range(member_count, t.member_from, t.member_to)
    ]
    return max(matching, default=None)


def effective_level(
    lead_count: int, member_count: int, flag: Optional[str], thresholds: List[Threshold]
) -> Optional[int]:
    """Return the level of an engineer in a leaf: expert, computed, aware, or None (FR-27)."""
    if flag == "expert":
        return 5
    if lead_count + member_count > 0:
        level = computed_level(lead_count, member_count, thresholds)
        if level is not None:
            return level
    if flag == "aware":
        return 1
    return None
