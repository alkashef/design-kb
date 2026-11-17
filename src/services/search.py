"""The search service: runs the experience search and builds the preview (FR-01, FR-05, D-04, D-10)."""

import logging
from dataclasses import dataclass
from typing import List

from src.domain import ranking
from src.domain.models import Employee
from src.domain.ranking import Hit
from src.services.employees import SkillLevel

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """One employee of a search with the reason for the match and the top leaves (FR-05)."""

    rank: int
    employee: Employee
    reason: str
    tags: List[SkillLevel]


class SearchService:
    """Finds the employees whose assignments match a query, through the store and the embedder."""

    def __init__(self, store, embedder, employees, result_limit: int):
        """Use store and embedder (real or fake), employees (an EmployeeService) and the limit."""
        self._store = store
        self._embedder = embedder
        self._employees = employees
        self._result_limit = result_limit

    def experience(self, query: str) -> List[SearchResult]:
        """Return the best employees for the query, best first; no query gives no results (D-28).

        Raises EmbeddingUnavailable when the embedding model does not answer.
        """
        if not query.strip():
            return []
        query_vector = self._embedder.embed([query.strip()])[0]
        assignments = {a.id: a for a in self._store.list_assignments()}
        matches = self._store.search_assignment_vectors(query_vector)
        hits = [
            Hit(m.employee_id, m.assignment_id, assignments[m.assignment_id].leaf_id, m.distance)
            for m in matches
            if m.assignment_id in assignments
        ]
        employees = {e.id: e for e in self._store.list_employees()}
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
