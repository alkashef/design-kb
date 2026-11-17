"""LanceStore: the only module that imports LanceDB (D-15, D-21)."""

import logging
from typing import Dict, List, Optional

import lancedb
import pyarrow as pa

from src.domain.models import (
    Assignment,
    AssignmentVector,
    Employee,
    Flag,
    Node,
    ProfileVector,
    Project,
    Threshold,
    VectorMatch,
)

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


ASSIGNMENTS_TABLE = "assignments"
ASSIGNMENTS_SCHEMA = pa.schema(
    [
        ("id", pa.string()),
        ("employee_id", pa.string()),
        ("project_id", pa.string()),
        ("leaf_id", pa.string()),
        ("participation", pa.string()),
        ("description", pa.string()),
    ]
)


FLAGS_TABLE = "flags"
FLAGS_SCHEMA = pa.schema(
    [
        ("employee_id", pa.string()),
        ("leaf_id", pa.string()),
        ("flag", pa.string()),
    ]
)


THRESHOLDS_TABLE = "thresholds"
THRESHOLDS_SCHEMA = pa.schema(
    [
        ("level", pa.int64()),
        ("lead_from", pa.int64()),
        ("lead_to", pa.int64()),
        ("member_from", pa.int64()),
        ("member_to", pa.int64()),
    ]
)


META_TABLE = "meta"
META_SCHEMA = pa.schema([("key", pa.string()), ("value", pa.string())])

ASSIGNMENT_VECTORS_TABLE = "assignment_vectors"
PROFILE_VECTORS_TABLE = "profile_vectors"


def _assignment_vectors_schema(vector_size: int) -> pa.Schema:
    """Return the schema of the table assignment_vectors for vectors of vector_size numbers."""
    return pa.schema(
        [
            ("assignment_id", pa.string()),
            ("employee_id", pa.string()),
            ("text", pa.string()),
            ("vector", pa.list_(pa.float32(), vector_size)),
        ]
    )


def _profile_vectors_schema(vector_size: int) -> pa.Schema:
    """Return the schema of the table profile_vectors for vectors of vector_size numbers."""
    return pa.schema(
        [
            ("employee_id", pa.string()),
            ("text", pa.string()),
            ("vector", pa.list_(pa.float32(), vector_size)),
        ]
    )


def _id_list(values: List[str]) -> str:
    """Return values as a quoted SQL list for an IN filter."""
    return "(" + ", ".join(_quote(value) for value in values) + ")"


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
        self._assignments = self._db.create_table(
            ASSIGNMENTS_TABLE, schema=ASSIGNMENTS_SCHEMA, exist_ok=True
        )
        self._flags = self._db.create_table(FLAGS_TABLE, schema=FLAGS_SCHEMA, exist_ok=True)
        self._thresholds = self._db.create_table(
            THRESHOLDS_TABLE, schema=THRESHOLDS_SCHEMA, exist_ok=True
        )
        self._meta = self._db.create_table(META_TABLE, schema=META_SCHEMA, exist_ok=True)
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

    def list_assignments(self) -> List[Assignment]:
        """Return all assignments."""
        return [Assignment(**row) for row in self._assignments.to_arrow().to_pylist()]

    def add_assignment(self, assignment: Assignment) -> None:
        """Write a new assignment."""
        self._assignments.add([vars(assignment)], mode="append")

    def update_assignment(self, assignment: Assignment) -> None:
        """Change every field of the assignment with the same ID."""
        values = {key: value for key, value in vars(assignment).items() if key != "id"}
        self._assignments.update(where=f"id = {_quote(assignment.id)}", values=values)

    def delete_assignment(self, assignment_id: str) -> None:
        """Delete one assignment."""
        self._assignments.delete(f"id = {_quote(assignment_id)}")

    def delete_assignments_of_employee(self, employee_id: str) -> None:
        """Delete the assignments of one employee."""
        self._assignments.delete(f"employee_id = {_quote(employee_id)}")

    def delete_assignments_of_project(self, project_id: str) -> None:
        """Delete the assignments of one project."""
        self._assignments.delete(f"project_id = {_quote(project_id)}")

    def list_flags(self) -> List[Flag]:
        """Return all flags."""
        return [Flag(**row) for row in self._flags.to_arrow().to_pylist()]

    def set_flag(self, flag: Flag) -> None:
        """Write the flag, and replace the one of the same employee and leaf."""
        self.delete_flag(flag.employee_id, flag.leaf_id)
        self._flags.add([vars(flag)], mode="append")

    def delete_flag(self, employee_id: str, leaf_id: str) -> None:
        """Delete the flag of one employee on one leaf."""
        self._flags.delete(f"employee_id = {_quote(employee_id)} AND leaf_id = {_quote(leaf_id)}")

    def delete_flags_of_employee(self, employee_id: str) -> None:
        """Delete the flags of one employee."""
        self._flags.delete(f"employee_id = {_quote(employee_id)}")

    def list_thresholds(self) -> List[Threshold]:
        """Return the saved thresholds; an empty list means the defaults apply (FR-32)."""
        return [Threshold(**row) for row in self._thresholds.to_arrow().to_pylist()]

    def replace_thresholds(self, thresholds: List[Threshold]) -> None:
        """Delete the saved thresholds and write the given ones (none writes nothing)."""
        self._thresholds.delete("level >= 0")
        if thresholds:
            self._thresholds.add([vars(t) for t in thresholds], mode="append")

    def get_meta(self) -> Dict[str, str]:
        """Return the rows of the table meta as a dict of key and value (D-27)."""
        return {row["key"]: row["value"] for row in self._meta.to_arrow().to_pylist()}

    def set_meta(self, values: Dict[str, str]) -> None:
        """Write the keys and values to the table meta, and replace the rows of the same keys."""
        if not values:
            return
        self._meta.delete(f"key IN {_id_list(list(values))}")
        self._meta.add([{"key": k, "value": v} for k, v in values.items()], mode="append")

    def list_assignment_vectors(self) -> List[AssignmentVector]:
        """Return all rows of the table assignment_vectors (D-35)."""
        rows = self._vector_rows(ASSIGNMENT_VECTORS_TABLE)
        return [AssignmentVector(**row) for row in rows]

    def list_profile_vectors(self) -> List[ProfileVector]:
        """Return all rows of the table profile_vectors (D-35)."""
        return [ProfileVector(**row) for row in self._vector_rows(PROFILE_VECTORS_TABLE)]

    def save_assignment_vectors(self, vectors: List[AssignmentVector]) -> None:
        """Write the vectors, and replace the rows of the same assignments."""
        if not vectors:
            return
        self.delete_assignment_vectors([v.assignment_id for v in vectors])
        schema = _assignment_vectors_schema(len(vectors[0].vector))
        self._add_vectors(ASSIGNMENT_VECTORS_TABLE, schema, [vars(v) for v in vectors])

    def delete_assignment_vectors(self, assignment_ids: List[str]) -> None:
        """Delete the vectors of the given assignments."""
        if assignment_ids:
            where = f"assignment_id IN {_id_list(assignment_ids)}"
            self._delete_vectors(ASSIGNMENT_VECTORS_TABLE, where)

    def delete_assignment_vectors_of_employee(self, employee_id: str) -> None:
        """Delete the assignment vectors of one employee."""
        self._delete_vectors(ASSIGNMENT_VECTORS_TABLE, f"employee_id = {_quote(employee_id)}")

    def save_profile_vector(self, vector: ProfileVector) -> None:
        """Write the profile vector, and replace the one of the same employee."""
        self.delete_profile_vector(vector.employee_id)
        schema = _profile_vectors_schema(len(vector.vector))
        self._add_vectors(PROFILE_VECTORS_TABLE, schema, [vars(vector)])

    def delete_profile_vector(self, employee_id: str) -> None:
        """Delete the profile vector of one employee."""
        self._delete_vectors(PROFILE_VECTORS_TABLE, f"employee_id = {_quote(employee_id)}")

    def search_assignment_vectors(
        self, query_vector: List[float], employee_ids: Optional[List[str]] = None
    ) -> List[VectorMatch]:
        """Return every assignment vector of the given employees (all when None), nearest first.

        The search is exact and uses the cosine distance, and it looks only at the vectors of the
        given employees (D-04, D-27, D-40).
        """
        if not self._has_table(ASSIGNMENT_VECTORS_TABLE) or employee_ids == []:
            return []
        table = self._db.open_table(ASSIGNMENT_VECTORS_TABLE)
        query = table.search(query_vector).metric("cosine")
        if employee_ids is not None:
            query = query.where(f"employee_id IN {_id_list(employee_ids)}", prefilter=True)
        rows = query.limit(table.count_rows()).to_list()
        return [VectorMatch(r["assignment_id"], r["employee_id"], r["_distance"]) for r in rows]

    def drop_vectors(self) -> None:
        """Delete both vector tables; the next write creates them with its vector size (D-27)."""
        self._db.drop_table(ASSIGNMENT_VECTORS_TABLE, ignore_missing=True)
        self._db.drop_table(PROFILE_VECTORS_TABLE, ignore_missing=True)

    def _has_table(self, name: str) -> bool:
        """Tell whether the table name exists in the folder."""
        return name in self._db.list_tables()

    def _vector_rows(self, name: str) -> List[dict]:
        """Return the rows of a vector table, or none when the table does not exist yet."""
        if not self._has_table(name):
            return []
        return self._db.open_table(name).to_arrow().to_pylist()

    def _add_vectors(self, name: str, schema: pa.Schema, rows: List[dict]) -> None:
        """Append rows to a vector table, and create the table first when it does not exist."""
        if self._has_table(name):
            self._db.open_table(name).add(rows, mode="append")
        else:
            self._db.create_table(name, data=rows, schema=schema)

    def _delete_vectors(self, name: str, where: str) -> None:
        """Delete the rows of a vector table that match the filter where."""
        if self._has_table(name):
            self._db.open_table(name).delete(where)
