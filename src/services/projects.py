"""The project service: lists, shows, creates, edits and deletes projects (FR-21, FR-28)."""

import logging
import uuid
from typing import List

from src.domain.models import Assignment, Project

logger = logging.getLogger(__name__)


class ProjectError(Exception):
    """Raised when an entry is rejected; the message is shown to the user."""


class UnknownProject(Exception):
    """Raised when a project ID is not in the store."""


class ProjectService:
    """Reads and changes projects through the store."""

    def __init__(self, store, indexing):
        """Use store (a LanceStore or a fake) and indexing (an IndexingService) for the vectors."""
        self._store = store
        self._indexing = indexing

    def list(self) -> List[Project]:
        """Return all projects, ordered by name."""
        return sorted(self._store.list_projects(), key=lambda p: (p.name.lower(), p.id))

    def get(self, project_id: str) -> Project:
        """Return the project, or raise UnknownProject."""
        for project in self._store.list_projects():
            if project.id == project_id:
                return project
        raise UnknownProject(project_id)

    def add(self, name: str, description: str, year: str, process_technology: str) -> str:
        """Add a project with a new random ID and return the ID."""
        project = self._build(uuid.uuid4().hex, name, description, year, process_technology)
        self._store.add_project(project)
        logger.info("Added a project.")
        return project.id

    def save(
        self, project_id: str, name: str, description: str, year: str, process_technology: str
    ) -> None:
        """Change the fields of a project, and embed its assignments again when needed (D-13)."""
        self.get(project_id)
        project = self._build(project_id, name, description, year, process_technology)
        vectors = self._indexing.embed_assignments(self._assignments_of(project_id), project)
        self._store.update_project(project)
        self._indexing.save_assignment_vectors(vectors)

    def delete(self, project_id: str) -> None:
        """Delete a project."""
        self.get(project_id)
        assignment_ids = [a.id for a in self._assignments_of(project_id)]
        self._store.delete_assignments_of_project(project_id)
        self._store.delete_project(project_id)
        self._indexing.delete_assignment_vectors(assignment_ids)
        logger.info("Deleted a project.")

    def _assignments_of(self, project_id: str) -> List[Assignment]:
        """Return the assignments of one project."""
        return [a for a in self._store.list_assignments() if a.project_id == project_id]

    @staticmethod
    def _build(
        project_id: str, name: str, description: str, year: str, process_technology: str
    ) -> Project:
        """Return the checked Project, or raise ProjectError."""
        if not name.strip():
            raise ProjectError("The name is required.")
        try:
            year_number = int(year.strip())
        except ValueError:
            raise ProjectError("The year must be a whole number.")
        return Project(
            project_id,
            name.strip(),
            description.strip(),
            year_number,
            process_technology.strip(),
        )
