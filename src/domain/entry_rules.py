"""The entry rules: decide whether an entry is valid and give the message (FR-24, FR-26, FR-41, FR-42).

Each function returns the message for a rejected entry, or None when the entry is valid.
"""

from typing import List, Optional

from src.domain import skill_tree
from src.domain.models import Assignment, Node

PARTICIPATIONS = ("lead", "member")
FLAG_VALUES = ("aware", "expert")


def leaf_problem(nodes: List[Node], leaf_id: str) -> Optional[str]:
    """Return a message when leaf_id is not a node, or is a node with children (FR-41)."""
    node = next((n for n in nodes if n.id == leaf_id), None)
    if node is None:
        return "Choose a skill from the list."
    if not skill_tree.is_leaf(nodes, leaf_id):
        return f"{node.name} has children. Choose one of its leaves."
    return None


def participation_problem(participation: str) -> Optional[str]:
    """Return a message when the participation is not lead or member."""
    if participation not in PARTICIPATIONS:
        return "Choose lead or member."
    return None


def duplicate_problem(existing: List[Assignment], candidate: Assignment) -> Optional[str]:
    """Return a message when another assignment has the employee, the project and the leaf (FR-42)."""
    for other in existing:
        if (
            other.id != candidate.id
            and other.employee_id == candidate.employee_id
            and other.project_id == candidate.project_id
            and other.leaf_id == candidate.leaf_id
        ):
            return "This employee already has an assignment for this skill in this project."
    return None


def flag_value_problem(flag: str) -> Optional[str]:
    """Return a message when the flag is not aware or expert (FR-26)."""
    if flag not in FLAG_VALUES:
        return "Choose Aware or Expert. Levels 2 to 4 come from projects."
    return None


def aware_problem(
    nodes: List[Node], assignments: List[Assignment], employee_id: str, leaf_id: str, flag: str
) -> Optional[str]:
    """Return a message when the Aware flag is set on a leaf where the employee has an assignment (FR-24)."""
    if flag != "aware":
        return None
    if any(a.employee_id == employee_id and a.leaf_id == leaf_id for a in assignments):
        name = next((n.name for n in nodes if n.id == leaf_id), leaf_id)
        return f"Aware is not allowed on {name}. This employee has an assignment in it."
    return None
