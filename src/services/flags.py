"""The flag service: sets and removes the Aware and Expert flags (FR-23, FR-24, FR-26, FR-40, FR-41)."""

import logging
from typing import List, Tuple

from src.domain import entry_rules, skill_tree
from src.domain.models import Flag, Node

logger = logging.getLogger(__name__)


class FlagError(Exception):
    """Raised when an entry is rejected; the message is shown to the user."""


class FlagService:
    """Reads and changes the flags of engineers through the store."""

    def __init__(self, store):
        """Use store (a LanceStore or a fake)."""
        self._store = store

    def for_engineer(self, engineer_id: str) -> List[Tuple[Flag, str]]:
        """Return the flags of one engineer with the path of the leaf, in tree order."""
        nodes = self._store.list_nodes()
        order = {n.id: index for index, (n, _depth) in enumerate(skill_tree.outline(nodes))}
        flags = [f for f in self._store.list_flags() if f.engineer_id == engineer_id]
        flags.sort(key=lambda f: order.get(f.leaf_id, len(order)))
        return [(f, skill_tree.path(nodes, f.leaf_id)) for f in flags]

    def leaf_options(self) -> List[Tuple[Node, str]]:
        """Return each leaf of the tree with its path, in tree order (FR-40)."""
        nodes = self._store.list_nodes()
        return [
            (node, skill_tree.path(nodes, node.id))
            for node, _depth in skill_tree.outline(nodes)
            if skill_tree.is_leaf(nodes, node.id)
        ]

    def set(self, engineer_id: str, leaf_id: str, flag: str) -> None:
        """Set the flag of an engineer on a leaf, or raise FlagError with the message."""
        nodes = self._store.list_nodes()
        problem = (
            entry_rules.flag_value_problem(flag)
            or entry_rules.leaf_problem(nodes, leaf_id)
            or entry_rules.aware_problem(
                nodes, self._store.list_assignments(), engineer_id, leaf_id, flag
            )
        )
        if problem:
            raise FlagError(problem)
        self._store.set_flag(Flag(engineer_id, leaf_id, flag))
        logger.info("Set a flag.")

    def remove(self, engineer_id: str, leaf_id: str) -> None:
        """Remove the flag of an engineer on a leaf."""
        self._store.delete_flag(engineer_id, leaf_id)
        logger.info("Removed a flag.")
