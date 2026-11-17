"""The search service: runs the experience search and builds the preview (FR-01, FR-05, D-04, D-10)."""

import logging
from dataclasses import dataclass
from typing import List

from src.domain import ranking
from src.domain.models import Employee
from src.domain.ranking import Hit
from src.services.employees import SkillLevel

logger = logging.getLogger(__name__)

TAG_LIMIT = 3


@dataclass
class SearchResult:
    """One employee of a search with the reason for the match and the top leaves (FR-05)."""

    rank: int
    employee: Employee
    reason: str
    tags: List[SkillLevel]


@dataclass
class SearchFilters:
    """The filters of a search: team, career level, and a leaf with its minimum level (FR-04)."""

    team: str = ""
    career_level: str = ""
    leaf_id: str = ""
    min_level: int = 1

    def is_set(self) -> bool:
        """Return True when at least one filter is set; min_level counts only with a leaf."""
        return bool(self.team or self.career_level or self.leaf_id)


class SearchService:
    """Finds the employees whose assignments match a query, through the store and the embedder."""

    def __init__(self, store, embedder, employees, result_limit: int):
        """Use store and embedder (real or fake), employees (an EmployeeService) and the limit."""
        self._store = store
        self._embedder = embedder
        self._employees = employees
        self._result_limit = result_limit

    def experience(self, query: str, filters: SearchFilters = None) -> List[SearchResult]:
        """Return the best employees for the query, best first (D-04, D-28).

        Step 1 keeps the employees that meet the filters. Step 2 ranks only their vectors.
        No query with filters lists all matching employees by name (FR-07); no query and no
        filter gives no results. Raises EmbeddingUnavailable when the embedding model does not answer.
        """
        filters = filters or SearchFilters()
        if not query.strip() and not filters.is_set():
            return []
        allowed = self._employees.matching(
            filters.team, filters.career_level, filters.leaf_id, filters.min_level
        )
        if not query.strip():
            return self._listing(allowed, filters.leaf_id)
        allowed_ids = {e.id for e in allowed}
        query_vector = self._embedder.embed([query.strip()])[0]
        assignments = {a.id: a for a in self._store.list_assignments()}
        matches = self._store.search_assignment_vectors(query_vector)
        hits = [
            Hit(m.employee_id, m.assignment_id, assignments[m.assignment_id].leaf_id, m.distance)
            for m in matches
            if m.assignment_id in assignments and m.employee_id in allowed_ids
        ]
        employees = {e.id: e for e in allowed}
        results = []
        for ranked in ranking.rank_employees(hits, self._result_limit):
            employee = employees.get(ranked.employee_id)
            if employee is None:
                continue
            results.append(
                SearchResult(
                    rank=len(results) + 1,
                    employee=employee,
                    reason=assignments[ranked.best_assignment_id].description,
                    tags=self._employees.levels_in(employee.id, ranked.leaf_ids),
                )
            )
        logger.info("Experience search found %d employees.", len(results))
        return results

    def gaps(self, query: str, filters: SearchFilters = None) -> List[SearchResult]:
        """Return the employees whose skill gaps match the query, best first (D-10, D-14).

        Only the profile vectors of the employees that meet the filters are ranked. The reason is
        the skill gap text, and the tags are the strongest skills. No query with filters lists all
        matching employees by name (FR-07); no query and no filter gives no results.
        """
        filters = filters or SearchFilters()
        if not query.strip() and not filters.is_set():
            return []
        allowed = self._employees.matching(
            filters.team, filters.career_level, filters.leaf_id, filters.min_level
        )
        if not query.strip():
            return self._listing(allowed, filters.leaf_id)
        employees = {e.id: e for e in allowed}
        query_vector = self._embedder.embed([query.strip()])[0]
        matches = [
            m
            for m in self._store.search_profile_vectors(query_vector)
            if m.employee_id in employees
        ][: self._result_limit]
        top = self._employees.top_skills([m.employee_id for m in matches])
        results = [
            SearchResult(number, employees[m.employee_id], employees[m.employee_id].skill_gaps,
                         top[m.employee_id][:TAG_LIMIT])
            for number, m in enumerate(matches, start=1)
        ]
        logger.info("Gap search found %d employees.", len(results))
        return results

    def _listing(self, employees: List[Employee], leaf_id: str) -> List[SearchResult]:
        """Return the employees as results in the given order, with no reason (FR-07)."""
        top = self._employees.top_skills([e.id for e in employees])
        results = []
        for number, employee in enumerate(employees, start=1):
            tags = self._employees.levels_in(employee.id, [leaf_id]) if leaf_id else top[employee.id]
            results.append(SearchResult(number, employee, "", tags[:TAG_LIMIT]))
        logger.info("Filter search found %d employees.", len(results))
        return results
