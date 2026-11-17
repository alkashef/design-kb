"""The skill tree service: reads and changes the tree (FR-30, FR-33)."""

import logging
import uuid
from typing import List, Tuple

from src.domain import skill_tree
from src.domain.models import Node

logger = logging.getLogger(__name__)


class SkillTreeError(Exception):
    """Raised when an entry is rejected; the message is shown to the user."""


class UnknownNode(Exception):
    """Raised when a node ID is not in the tree."""


class SkillTreeService:
    """Adds, saves and deletes nodes of the skill tree through the store."""

    def __init__(self, store):
        """Use store (a LanceStore or a fake) for the nodes."""
        self._store = store

    def outline(self) -> List[Tuple[Node, int, bool]]:
        """Return every node with its depth and its leaf flag, in outline order."""
        nodes = self._store.list_nodes()
        return [(n, depth, skill_tree.is_leaf(nodes, n.id)) for n, depth in skill_tree.outline(nodes)]

    def get(self, node_id: str) -> Node:
        """Return the node, or raise UnknownNode."""
        for node in self._store.list_nodes():
            if node.id == node_id:
                return node
        raise UnknownNode(node_id)

    def path(self, node_id: str) -> str:
        """Return the path of the node, such as 'Circuit design / Clocking / PLL'."""
        return skill_tree.path(self._store.list_nodes(), node_id)

    def is_leaf(self, node_id: str) -> bool:
        """Tell whether the node has no children."""
        return skill_tree.is_leaf(self._store.list_nodes(), node_id)

    def add(self, parent_id: str, name: str, description: str) -> str:
        """Add a node below parent_id (empty for top level) and return its ID."""
        nodes = self._store.list_nodes()
        clean_name = self._clean_name(name)
        if parent_id and not any(n.id == parent_id for n in nodes):
            raise UnknownNode(parent_id)
        position = len(skill_tree.children_of(nodes, parent_id))
        node = Node(uuid.uuid4().hex, parent_id, clean_name, description.strip(), position)
        self._store.add_node(node)
        logger.info("Added a skill tree node.")
        return node.id

    def save(self, node_id: str, name: str, description: str) -> None:
        """Rename and describe a node."""
        self.get(node_id)
        self._store.update_node(node_id, self._clean_name(name), description.strip())

    def delete(self, node_id: str) -> None:
        """Delete a node with no children; refuse otherwise (FR-33)."""
        node = self.get(node_id)
        if not self.is_leaf(node_id):
            raise SkillTreeError(
                f"{node.name} has children. Delete or move them before you delete this skill."
            )
        self._store.delete_node(node_id)
        logger.info("Deleted a skill tree node.")

    @staticmethod
    def _clean_name(name: str) -> str:
        """Return the trimmed name, or raise SkillTreeError when it is empty."""
        clean = name.strip()
        if not clean:
            raise SkillTreeError("The name is required.")
        return clean

