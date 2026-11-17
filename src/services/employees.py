"""The employee service: lists, shows, creates, edits and deletes employees (FR-10, FR-20, FR-28)."""

import logging
from dataclasses import dataclass
from typing import List

from src.domain.models import CAREER_LEVELS, Employee

logger = logging.getLogger(__name__)

ID_PREFIX = "E-"


class EmployeeError(Exception):
    """Raised when an entry is rejected; the message is shown to the user."""


class UnknownEmployee(Exception):
    """Raised when an employee ID is not in the store."""


@dataclass
class EmployeePage:
    """One page of the Employees list."""

    rows: List[Employee]
    page: int
    page_count: int
    total: int


class EmployeeService:
    """Reads and changes employees through the store."""

    def __init__(self, store, page_size: int):
        """Use store (a LanceStore or a fake) and the number of rows on one page."""
        self._store = store
        self._page_size = page_size

    def teams(self) -> List[str]:
        """Return the distinct team names, sorted."""
        return sorted({e.team for e in self._store.list_employees() if e.team})

    def list(
        self, text: str = "", team: str = "", career_level: str = "", page: int = 1
    ) -> EmployeePage:
        """Return one page of the employees that match the filters, ordered by ID."""
        needle = text.strip().lower()
        matches = [
            e
            for e in sorted(self._store.list_employees(), key=lambda e: e.id)
            if (not needle or needle in e.name.lower() or needle in e.id.lower())
            and (not team or e.team == team)
            and (not career_level or e.career_level == career_level)
        ]
        page_count = max(1, -(-len(matches) // self._page_size))
        page = min(max(page, 1), page_count)
        start = (page - 1) * self._page_size
        rows = matches[start : start + self._page_size]
        return EmployeePage(rows, page, page_count, len(matches))

    def get(self, employee_id: str) -> Employee:
        """Return the employee, or raise UnknownEmployee."""
        for employee in self._store.list_employees():
            if employee.id == employee_id:
                return employee
        raise UnknownEmployee(employee_id)

    def add(self, name: str, job_title: str, career_level: str, team: str, skill_gaps: str) -> str:
        """Add an employee with the next free ID and return the ID."""
        employee = self._build(self._next_id(), name, job_title, career_level, team, skill_gaps)
        self._store.add_employee(employee)
        logger.info("Added an employee.")
        return employee.id

    def save(
        self,
        employee_id: str,
        name: str,
        job_title: str,
        career_level: str,
        team: str,
        skill_gaps: str,
    ) -> None:
        """Change the fields of an employee."""
        self.get(employee_id)
        employee = self._build(employee_id, name, job_title, career_level, team, skill_gaps)
        self._store.update_employee(employee)

    def delete(self, employee_id: str) -> None:
        """Delete an employee."""
        self.get(employee_id)
        self._store.delete_assignments_of_employee(employee_id)
        self._store.delete_employee(employee_id)
        logger.info("Deleted an employee.")

    def _next_id(self) -> str:
        """Return the ID after the highest one in use, such as E-0003."""
        numbers = [
            int(e.id[len(ID_PREFIX) :])
            for e in self._store.list_employees()
            if e.id.startswith(ID_PREFIX) and e.id[len(ID_PREFIX) :].isdigit()
        ]
        return f"{ID_PREFIX}{max(numbers, default=0) + 1:04d}"

    @staticmethod
    def _build(
        employee_id: str, name: str, job_title: str, career_level: str, team: str, skill_gaps: str
    ) -> Employee:
        """Return the checked Employee, or raise EmployeeError."""
        if not name.strip():
            raise EmployeeError("The name is required.")
        if career_level not in CAREER_LEVELS:
            raise EmployeeError("Choose a career level from the list.")
        return Employee(
            employee_id,
            name.strip(),
            job_title.strip(),
            career_level,
            team.strip(),
            skill_gaps.strip(),
        )
