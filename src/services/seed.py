"""The seed service: loads the seed data into an empty store (NFR-04, D-26)."""

import logging

from src.domain import seed_data
from src.domain.models import EmbeddingUnavailable

logger = logging.getLogger(__name__)


class SeedService:
    """Writes the seed records and their vectors when the store has no employee."""

    def __init__(self, store, indexing):
        """Use store (a LanceStore or a fake) and indexing (an IndexingService) for the vectors."""
        self._store = store
        self._indexing = indexing

    def load_if_empty(self) -> bool:
        """Load the seed data when the store has no employee; return true when it loaded.

        The vectors are embedded before any record is written (D-27). When the embedding model does
        not answer, nothing is written, and the next start tries again.
        """
        if self._store.list_employees():
            return False
        seed = seed_data.build()
        try:
            assignment_vectors = self._embed_assignments(seed)
            profiles = [(e, self._indexing.embed_profile(e)) for e in seed.employees]
        except EmbeddingUnavailable:
            logger.warning("The embedding model does not answer; the seed data was not loaded.")
            return False
        self._write_records(seed)
        self._indexing.save_assignment_vectors(assignment_vectors)
        for employee, profile in profiles:
            self._indexing.save_profile(employee, profile)
        logger.info(
            "Loaded the seed data: %d employees, %d projects, %d assignments.",
            len(seed.employees),
            len(seed.projects),
            len(seed.assignments),
        )
        return True

    def _embed_assignments(self, seed):
        """Embed the assignments of the seed, one project at a time, and return their vectors."""
        vectors = []
        for project in seed.projects:
            of_project = [a for a in seed.assignments if a.project_id == project.id]
            vectors.extend(
                self._indexing.embed_assignments(of_project, project=project, nodes=seed.nodes)
            )
        return vectors

    def _write_records(self, seed) -> None:
        """Write the nodes, the employees, the projects, the assignments and the flags."""
        for node in seed.nodes:
            self._store.add_node(node)
        for employee in seed.employees:
            self._store.add_employee(employee)
        for project in seed.projects:
            self._store.add_project(project)
        for assignment in seed.assignments:
            self._store.add_assignment(assignment)
        for flag in seed.flags:
            self._store.set_flag(flag)
