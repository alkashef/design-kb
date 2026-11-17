"""The assignment service: lists, creates, edits and deletes assignments (FR-22, FR-28, FR-40 to FR-42)."""

import logging
import uuid
from dataclasses import dataclass
from typing import List, Tuple

from src.domain import entry_rules, skill_tree
from src.domain.models import Assignment, Employee, Node

logger = logging.getLogger(__name__)


class AssignmentError(Exception):
    """Raised when an entry is rejected; the message is shown to the user."""


class UnknownAssignment(Exception):
    """Raised when an assignment ID is not in the store."""


@dataclass
class AssignmentRow:
    """An assignment with the names that a page shows."""

    assignment: Assignment
    employee_name: str
    project_name: str
    project_year: int
    process_technology: str
    leaf_path: str


class AssignmentService:
    """Reads and changes assignments through the store."""

    def __init__(self, store, indexing):
        """Use store (a LanceStore or a fake) and indexing (an IndexingService) for the vectors."""
        self._store = store
        self._indexing = indexing

    def for_project(self, project_id: str) -> List[AssignmentRow]:
        """Return the rows of one project, ordered by employee name and leaf path."""
        rows = self._rows(lambda a: a.project_id == project_id)
        return sorted(rows, key=lambda r: (r.employee_name.lower(), r.leaf_path.lower()))

    def for_employee(self, employee_id: str) -> List[AssignmentRow]:
        """Return the rows of one employee, ordered by project year (newest first) and name."""
        rows = self._rows(lambda a: a.employee_id == employee_id)
        return sorted(rows, key=lambda r: (-r.project_year, r.project_name.lower(), r.leaf_path))

    def get(self, assignment_id: str) -> Assignment:
        """Return the assignment, or raise UnknownAssignment."""
        for assignment in self._store.list_assignments():
            if assignment.id == assignment_id:
                return assignment
        raise UnknownAssignment(assignment_id)

    def leaf_options(self) -> List[Tuple[Node, str]]:
        """Return each leaf of the tree with its path, in tree order (FR-40)."""
        nodes = self._store.list_nodes()
        return [
            (node, skill_tree.path(nodes, node.id))
            for node, _depth in skill_tree.outline(nodes)
            if skill_tree.is_leaf(nodes, node.id)
        ]

    def employee_options(self) -> List[Employee]:
        """Return all employees, ordered by name."""
        return sorted(self._store.list_employees(), key=lambda e: (e.name.lower(), e.id))

    def add(
        self, project_id: str, employee_id: str, leaf_id: str, participation: str, description: str
    ) -> str:
        """Add an assignment with a new random ID and return the ID."""
        if not any(e.id == employee_id for e in self._store.list_employees()):
            raise AssignmentError("Choose an employee from the list.")
        assignment = Assignment(
            uuid.uuid4().hex, employee_id, project_id, leaf_id, participation, description.strip()
        )
        self._check(assignment)
        vectors = self._indexing.embed_assignments([assignment])
        self._store.add_assignment(assignment)
        self._indexing.save_assignment_vectors(vectors)
        logger.info("Added an assignment.")
        return assignment.id

    def save(self, assignment_id: str, leaf_id: str, participation: str, description: str) -> None:
        """Change the leaf, the participation and the description of an assignment."""
        old = self.get(assignment_id)
        assignment = Assignment(
            old.id, old.employee_id, old.project_id, leaf_id, participation, description.strip()
        )
        self._check(assignment)
        vectors = self._indexing.embed_assignments([assignment])
        self._store.update_assignment(assignment)
        self._indexing.save_assignment_vectors(vectors)

    def delete(self, assignment_id: str) -> None:
        """Delete an assignment."""
        self.get(assignment_id)
        self._store.delete_assignment(assignment_id)
        self._indexing.delete_assignment_vectors([assignment_id])
        logger.info("Deleted an assignment.")

    def _check(self, assignment: Assignment) -> None:
        """Raise AssignmentError with the message of the first rule that the assignment breaks."""
        problem = (
            entry_rules.leaf_problem(self._store.list_nodes(), assignment.leaf_id)
            or entry_rules.participation_problem(assignment.participation)
            or entry_rules.duplicate_problem(self._store.list_assignments(), assignment)
        )
        if problem:
            raise AssignmentError(problem)

    def _rows(self, wanted) -> List[AssignmentRow]:
        """Return the rows of the assignments for which wanted(assignment) is true."""
        nodes = self._store.list_nodes()
        employees = {e.id: e for e in self._store.list_employees()}
        projects = {p.id: p for p in self._store.list_projects()}
        return [
            AssignmentRow(
                a,
                employees[a.employee_id].name,
                projects[a.project_id].name,
                projects[a.project_id].year,
                projects[a.project_id].process_technology,
                skill_tree.path(nodes, a.leaf_id),
            )
            for a in self._store.list_assignments()
            if wanted(a) and a.employee_id in employees and a.project_id in projects
        ]
