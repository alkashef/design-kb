"""Unit tests of the ranking of engineers (M12): FR-01, FR-05, D-11."""

from src.domain import ranking
from src.domain.ranking import Hit


def hit(engineer_id, assignment_id, leaf_id, distance):
    """Make one vector hit with invented IDs."""
    return Hit(
        engineer_id=engineer_id,
        assignment_id=assignment_id,
        leaf_id=leaf_id,
        distance=distance,
    )


def test_fr_01_rank_engineers_puts_the_smallest_best_distance_first():
    hits = [
        hit("E-0001", "a-1", "leaf-a", 0.50),
        hit("E-0001", "a-2", "leaf-b", 0.90),
        hit("E-0002", "a-3", "leaf-a", 0.20),
        hit("E-0003", "a-4", "leaf-c", 0.40),
    ]

    ranked = ranking.rank_engineers(hits, limit=10)

    assert [item.engineer_id for item in ranked] == ["E-0002", "E-0003", "E-0001"]


def test_d_11_rank_engineers_uses_the_best_assignment_of_each_engineer():
    hits = [
        hit("E-0001", "a-worse", "leaf-b", 0.90),
        hit("E-0001", "a-best", "leaf-a", 0.50),
    ]

    ranked = ranking.rank_engineers(hits, limit=10)

    assert [item.best_assignment_id for item in ranked] == ["a-best"]


def test_fr_01_rank_engineers_returns_at_most_limit_engineers():
    hits = [hit(f"E-000{number}", f"a-{number}", "leaf-a", number / 10) for number in range(1, 5)]

    ranked = ranking.rank_engineers(hits, limit=2)

    assert [item.engineer_id for item in ranked] == ["E-0001", "E-0002"]


def test_fr_05_rank_engineers_keeps_at_most_3_leaves_each_one_time():
    hits = [
        hit("E-0001", "a-5", "leaf-d", 0.50),
        hit("E-0001", "a-3", "leaf-a", 0.30),
        hit("E-0001", "a-1", "leaf-a", 0.10),
        hit("E-0001", "a-2", "leaf-b", 0.20),
        hit("E-0001", "a-4", "leaf-c", 0.40),
    ]

    ranked = ranking.rank_engineers(hits, limit=10)

    assert [list(item.leaf_ids) for item in ranked] == [["leaf-a", "leaf-b", "leaf-c"]]
