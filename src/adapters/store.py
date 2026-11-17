"""LanceStore: the only module that imports LanceDB (D-15, D-21)."""

import logging
from typing import List

import lancedb
import pyarrow as pa

from src.domain.models import Employee, Node, Project

logger = logging.getLogger(__name__)

NODES_TABLE = "nodes"
NODES_SCHEMA = pa.schema(
    [
        ("id", pa.string()),
        ("parent_id", pa.string()),
        ("name", pa.string()),
        ("description", pa.string()),
        ("position", pa.int64()),
    ]
)


EMPLOYEES_TABLE = "employees"
EMPLOYEES_SCHEMA = pa.schema(
    [
        ("id", pa.string()),
        ("name", pa.string()),
        ("job_title", pa.string()),
        ("career_level", pa.string()),
        ("team", pa.string()),
        ("skill_gaps", pa.string()),
    ]
)


PROJECTS_TABLE = "projects"
PROJECTS_SCHEMA = pa.schema(
    [
        ("id", pa.string()),
        ("name", pa.string()),
        ("description", pa.string()),
        ("year", pa.int64()),
        ("process_technology", pa.string()),
    ]
)


def _quote(value: str) -> str:
    """Return value as a quoted SQL text for a filter."""
    return "'" + value.replace("'", "''") + "'"


class LanceStore:
    """Opens the LanceDB folder and reads and writes its tables."""

    def __init__(self, data_dir: str):
        """Open or create the LanceDB folder data_dir and its tables."""
        self._db = lancedb.connect(data_dir)
        self._nodes = self._db.create_table(NODES_TABLE, schema=NODES_SCHEMA, exist_ok=True)
        self._employees = self._db.create_table(
            EMPLOYEES_TABLE, schema=EMPLOYEES_SCHEMA, exist_ok=True
        )
        self._projects = self._db.create_table(
            PROJECTS_TABLE, schema=PROJECTS_SCHEMA, exist_ok=True
        )
        logger.info("Opened the store.")

    def list_nodes(self) -> List[Node]:
        """Return all nodes of the skill tree."""
        return [Node(**row) for row in self._nodes.to_arrow().to_pylist()]

    def add_node(self, node: Node) -> None:
        """Write a new node."""
        self._nodes.add([vars(node)], mode="append")

    def update_node(self, node_id: str, name: str, description: str) -> None:
        """Change the name and the description of a node."""
        self._nodes.update(
            where=f"id = {_quote(node_id)}", values={"name": name, "description": description}
        )

    def delete_node(self, node_id: str) -> None:
        """Delete one node."""
        self._nodes.delete(f"id = {_quote(node_id)}")

    def list_employees(self) -> List[Employee]:
        """Return all employees."""
        return [Employee(**row) for row in self._employees.to_arrow().to_pylist()]

    def add_employee(self, employee: Employee) -> None:
        """Write a new employee."""
        self._employees.add([vars(employee)], mode="append")

    def update_employee(self, employee: Employee) -> None:
        """Change every field of the employee with the same ID."""
        values = {key: value for key, value in vars(employee).items() if key != "id"}
        self._employees.update(where=f"id = {_quote(employee.id)}", values=values)

    def delete_employee(self, employee_id: str) -> None:
        """Delete one employee."""
        self._employees.delete(f"id = {_quote(employee_id)}")

    def list_projects(self) -> List[Project]:
        """Return all projects."""
        return [Project(**row) for row in self._projects.to_arrow().to_pylist()]

    def add_project(self, project: Project) -> None:
        """Write a new project."""
        self._projects.add([vars(project)], mode="append")

    def update_project(self, project: Project) -> None:
        """Change every field of the project with the same ID."""
        values = {key: value for key, value in vars(project).items() if key != "id"}
        self._projects.update(where=f"id = {_quote(project.id)}", values=values)

    def delete_project(self, project_id: str) -> None:
        """Delete one project."""
        self._projects.delete(f"id = {_quote(project_id)}")
