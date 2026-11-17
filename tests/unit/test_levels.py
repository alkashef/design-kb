"""Unit tests of the level rules (spec section 2.5, FR-25, FR-27, FR-32)."""

from src.domain import levels
from src.domain.models import Threshold


def test_fr_25_lead_in_3_projects_gives_level_4():
    assert levels.computed_level(3, 0, levels.default_thresholds()) == 4


def test_fr_25_lead_in_1_project_gives_level_3():
    assert levels.computed_level(1, 0, levels.default_thresholds()) == 3


def test_fr_25_member_in_1_project_gives_level_2():
    assert levels.computed_level(0, 1, levels.default_thresholds()) == 2


def test_fr_25_counts_in_no_range_give_no_level():
    assert levels.computed_level(0, 0, levels.default_thresholds()) is None


def test_fr_25_highest_matching_level_wins():
    overlapping = [
        Threshold(level=2, lead_from=0, lead_to=None, member_from=0, member_to=None),
        Threshold(level=3, lead_from=1, lead_to=None, member_from=0, member_to=None),
        Threshold(level=4, lead_from=2, lead_to=None, member_from=0, member_to=None),
    ]
    assert levels.computed_level(2, 1, overlapping) == 4
    assert levels.computed_level(1, 1, overlapping) == 3


def test_fr_25_assignment_overrides_the_aware_flag():
    thresholds = levels.default_thresholds()
    assert levels.effective_level(0, 1, "aware", thresholds) == 2


def test_fr_27_expert_flag_gives_level_5_over_the_computed_level():
    thresholds = levels.default_thresholds()
    assert levels.effective_level(3, 0, "expert", thresholds) == 5


def test_fr_32_default_thresholds_equal_spec_section_2_5():
    by_level = {t.level: t for t in levels.default_thresholds()}
    assert set(by_level) == {2, 3, 4}
    assert (by_level[2].lead_from, by_level[2].lead_to) == (0, 0)
    assert (by_level[2].member_from, by_level[2].member_to) == (1, None)
    assert (by_level[3].lead_from, by_level[3].lead_to) == (1, 2)
    assert (by_level[3].member_from, by_level[3].member_to) == (0, None)
    assert (by_level[4].lead_from, by_level[4].lead_to) == (3, None)
    assert (by_level[4].member_from, by_level[4].member_to) == (0, None)
    assert levels.LEVEL_NAMES == {
        1: "Aware", 2: "Hands-on", 3: "Lead", 4: "Senior lead", 5: "Expert",
    }
