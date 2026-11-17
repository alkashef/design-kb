"""The tree rules: leaves, leaves under a node, paths and the outline order (spec 2.2, D-06)."""

from typing import List, Tuple

from src.domain.models import Node

PATH_SEPARATOR = " / "


def children_of(nodes: List[Node], parent_id: str) -> List[Node]:
    """Return the nodes below parent_id, ordered by position."""
    return sorted((n for n in nodes if n.parent_id == parent_id), key=lambda n: n.position)


def is_leaf(nodes: List[Node], node_id: str) -> bool:
    """Tell whether no node has node_id as its parent."""
    return not any(n.parent_id == node_id for n in nodes)


def leaves_under(nodes: List[Node], node_id: str) -> List[Node]:
    """Return the leaves below the node in tree order; a leaf gives itself."""
    node = next(n for n in nodes if n.id == node_id)
    if is_leaf(nodes, node_id):
        return [node]
    leaves: List[Node] = []
    for child in children_of(nodes, node_id):
        leaves.extend(leaves_under(nodes, child.id))
    return leaves


def path(nodes: List[Node], node_id: str) -> str:
    """Return the names from the top-level node to the node, joined with ' / '."""
    by_id = {n.id: n for n in nodes}
    names: List[str] = []
    current = by_id.get(node_id)
    while current is not None:
        names.append(current.name)
        current = by_id.get(current.parent_id)
    return PATH_SEPARATOR.join(reversed(names))


def outline(nodes: List[Node]) -> List[Tuple[Node, int]]:
    """Return every node with its depth, parents before their children, in tree order."""
    rows: List[Tuple[Node, int]] = []

    def walk(parent_id: str, depth: int) -> None:
        """Add the children of parent_id, each followed by its own children."""
        for child in children_of(nodes, parent_id):
            rows.append((child, depth))
            walk(child.id, depth + 1)

    walk("", 0)
    return rows
