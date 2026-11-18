"""Route tests of the foldable outline of the Skill tree page (M20): FR-30 and D-19."""

from html.parser import HTMLParser

from builders import add_node

VOID_TAGS = {"input", "br", "img", "meta", "link", "hr"}


class FoldCollector(HTMLParser):
    """Records each <details> (open or not, its summary rows, its inner rows) and every outline row."""

    def __init__(self):
        """Start with no elements."""
        super().__init__()
        self._stack: list[tuple[str, int | None]] = []  # (tag, details index or None)
        self.details: list[dict] = []
        self.row_ids: list[str] = []
        self.row_in_summary: dict[str, int] = {}
        self.row_parent_details: dict[str, list[int]] = {}
        self.row_leaf: dict[str, bool] = {}
        self.row_in_details: dict[str, bool] = {}

    def _open_details(self) -> list[int]:
        """Return the indexes of the open <details> elements, outermost first."""
        return [index for tag, index in self._stack if tag == "details"]

    def _in_summary(self) -> bool:
        """Return True while inside a <summary>."""
        return any(tag == "summary" for tag, _ in self._stack)

    def handle_starttag(self, tag, attrs):
        """Track the stack, and note each details element and outline row."""
        attributes = dict(attrs)
        index = None
        if tag == "details":
            index = len(self.details)
            self.details.append({"open": "open" in attributes, "summary_rows": [], "rows": []})
        node_id = attributes.get("data-node-id")
        if node_id is not None:
            enclosing = self._open_details()
            self.row_ids.append(node_id)
            self.row_leaf[node_id] = attributes.get("data-leaf") == "true"
            self.row_parent_details[node_id] = enclosing
            self.row_in_details[node_id] = bool(enclosing)
            for number in enclosing:
                self.details[number]["rows"].append(node_id)
            if self._in_summary() and enclosing:
                self.details[enclosing[-1]]["summary_rows"].append(node_id)
        if tag not in VOID_TAGS:
            self._stack.append((tag, index))

    def handle_endtag(self, tag):
        """Close the matching element."""
        for position in range(len(self._stack) - 1, -1, -1):
            if self._stack[position][0] == tag:
                del self._stack[position:]
                break


def read_fold(client, path):
    """Fetch a page and return the parsed fold structure."""
    response = client.get(path)
    assert response.status_code == 200
    collector = FoldCollector()
    collector.feed(response.text)
    return collector


def build_tree(client):
    """Add two top-level nodes; the first has a branch with a leaf at depth 2."""
    top = add_node(client, "Analog design")
    branch = add_node(client, "Clocking", parent_id=top)
    leaf = add_node(client, "PLL", parent_id=branch)
    other_top = add_node(client, "Digital design")
    other_leaf = add_node(client, "Synthesis", parent_id=other_top)
    return {"top": top, "branch": branch, "leaf": leaf, "other_top": other_top, "other_leaf": other_leaf}


def owning_details(page, node_id):
    """Return the details element whose summary holds the row of node_id, or None."""
    for details in page.details:
        if node_id in details["summary_rows"]:
            return details
    return None


def test_fr_30_outline_folds_each_parent_node(client):
    ids = build_tree(client)

    page = read_fold(client, "/skill-tree")

    for parent_id, child_id in [
        (ids["top"], ids["branch"]),
        (ids["branch"], ids["leaf"]),
        (ids["other_top"], ids["other_leaf"]),
    ]:
        details = owning_details(page, parent_id)
        assert details is not None, f"node {parent_id} has children but no <summary> row in a <details>"
        assert child_id in details["rows"], "the child row is not inside the parent's <details>"
    for leaf_id in (ids["leaf"], ids["other_leaf"]):
        assert owning_details(page, leaf_id) is None, "a leaf must not have its own <details>"


def test_fr_30_outline_opens_path_to_selected_node(client):
    ids = build_tree(client)

    page = read_fold(client, f"/skill-tree/{ids['leaf']}")

    for ancestor_id in (ids["top"], ids["branch"]):
        details = owning_details(page, ancestor_id)
        assert details is not None and details["open"], f"ancestor {ancestor_id} is not open"
    other = owning_details(page, ids["other_top"])
    assert other is not None and not other["open"], "a branch that is not an ancestor must be folded"


def test_fr_30_outline_folded_without_selection(client):
    ids = build_tree(client)

    page = read_fold(client, "/skill-tree")

    assert page.details, "the outline has no <details> element"
    assert not any(details["open"] for details in page.details)
    assert ids["top"] in page.row_ids
    assert ids["other_top"] in page.row_ids
