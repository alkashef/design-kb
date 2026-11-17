"""LanceStore: the only module that imports LanceDB (D-15, D-21)."""

import logging
from typing import List

import lancedb
import pyarrow as pa

from src.domain.models import Node

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


def _quote(value: str) -> str:
    """Return value as a quoted SQL text for a filter."""
    return "'" + value.replace("'", "''") + "'"


class LanceStore:
    """Opens the LanceDB folder and reads and writes its tables."""

    def __init__(self, data_dir: str):
        """Open or create the LanceDB folder data_dir and its tables."""
        self._db = lancedb.connect(data_dir)
        self._nodes = self._db.create_table(NODES_TABLE, schema=NODES_SCHEMA, exist_ok=True)
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
