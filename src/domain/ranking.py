"""Ranks employees from the hits of a vector search (FR-01, FR-05, D-11, D-39)."""

from dataclasses import dataclass
from typing import Dict, List

MAX_LEAVES = 3


@dataclass
class Hit:
    """One assignment vector that matched a query, with its distance (smaller is nearer)."""

    employee_id: str
    assignment_id: str
    leaf_id: str
    distance: float


@dataclass
class RankedEmployee:
    """An employee with the best matching assignment and the leaves of the best hits."""

    employee_id: str
    best_assignment_id: str
    leaf_ids: List[str]


def _group_by_employee(hits: List[Hit]) -> Dict[str, List[Hit]]:
    """Return the hits of each employee, nearest first."""
    groups: Dict[str, List[Hit]] = {}
    for hit in sorted(hits, key=lambda h: h.distance):
        groups.setdefault(hit.employee_id, []).append(hit)
    return groups


def _top_leaves(nearest_first: List[Hit]) -> List[str]:
    """Return at most MAX_LEAVES leaves of the hits, each one time, in the order of the hits."""
    leaves: List[str] = []
    for hit in nearest_first:
        if hit.leaf_id not in leaves:
            leaves.append(hit.leaf_id)
    return leaves[:MAX_LEAVES]


def rank_employees(hits: List[Hit], limit: int) -> List[RankedEmployee]:
    """Return at most limit employees, the one with the nearest assignment first (D-11)."""
    groups = _group_by_employee(hits)
    # Each group is nearest first, so group[0] is the best hit of its employee.
    order = sorted(groups, key=lambda employee_id: (groups[employee_id][0].distance, employee_id))
    return [
        RankedEmployee(
            employee_id, groups[employee_id][0].assignment_id, _top_leaves(groups[employee_id])
        )
        for employee_id in order[:limit]
    ]
