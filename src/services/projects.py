"""The project service: lists, shows, creates, edits and deletes projects (FR-21, FR-28)."""

import logging
import uuid
from typing import List

from src.domain.models import Project

logger = logging.getLogger(__name__)


class ProjectError(Exception):
    """Raised when an entry is rejected; the message is shown to the user."""


class UnknownProject(Exception):
    """Raised when a project ID is not in the store."""


class ProjectService:
    """Reads and changes projects through the store."""

    def __init__(self, store):
        """Use store (a LanceStore or a fake)."""
        self._store = store

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
        """Change the fields of a project."""
        self.get(project_id)
        self._store.update_project(
            self._build(project_id, name, description, year, process_technology)
        )

    def delete(self, project_id: str) -> None:
        """Delete a project."""
        self.get(project_id)
        self._store.delete_project(project_id)
        logger.info("Deleted a project.")

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
