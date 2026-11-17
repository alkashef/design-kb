"""Builds the texts that are embedded: an assignment vector (D-08) and a profile vector (D-09)."""

from src.domain.models import Assignment, Employee, Node, Project

LINE_SEPARATOR = "\n"


def assignment_text(assignment: Assignment, project: Project, leaf: Node, leaf_path: str) -> str:
    """Return the 6 lines of an assignment vector, in the order of docs/design.md, Data storage."""
    lines = [
        leaf.name,
        leaf.description,
        leaf_path,
        assignment.participation,
        assignment.description,
        project.process_technology,
    ]
    return LINE_SEPARATOR.join(lines)


def profile_text(employee: Employee) -> str:
    """Return the text of a profile vector: the skill gaps, or an empty text when there are none."""
    return employee.skill_gaps.strip()
