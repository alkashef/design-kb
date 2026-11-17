"""Route tests of the skill tree editor (M3): FR-30 and FR-33."""

from html.parser import HTMLParser


class OutlineCollector(HTMLParser):
    """Collects the outline rows (data-node-id, data-leaf) and the text of a page."""

    def __init__(self):
        """Start with no rows."""
        super().__init__()
        self.rows: list[tuple[str, bool]] = []
        self.text: list[str] = []
        self.values: list[str] = []
        self.alerts = 0

    def handle_starttag(self, tag, attrs):
        """Keep each outline row, each input value and each alert."""
        attributes = dict(attrs)
        if "data-node-id" in attributes:
            self.rows.append((attributes["data-node-id"], attributes.get("data-leaf") == "true"))
        if attributes.get("value"):
            self.values.append(attributes["value"])
        if attributes.get("role") == "alert":
            self.alerts += 1

    def handle_data(self, data):
        """Keep the text of the page."""
        self.text.append(data)

    @property
    def page_text(self) -> str:
        """Return all text and input values of the page as one string."""
        return " ".join(self.text + self.values)


def read_page(html: str) -> OutlineCollector:
    """Parse a page and return what the tests look at."""
    collector = OutlineCollector()
    collector.feed(html)
    return collector


def add_node(client, name, parent_id="", description=""):
    """Post a new node and return its ID, taken from the redirect address."""
    response = client.post(
        "/skill-tree/nodes",
        data={"parent_id": parent_id, "name": name, "description": description},
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/skill-tree/")
    return location.rsplit("/", 1)[1]


def outline(client):
    """Return the parsed Skill tree page with no node selected."""
    response = client.get("/skill-tree")
    assert response.status_code == 200
    return read_page(response.text)


def test_fr_30_add_top_level_node_shows_in_the_outline(client):
    node_id = add_node(client, "Analog design")

    page = outline(client)

    assert (node_id, True) in page.rows
    assert "Analog design" in page.page_text


def test_fr_30_add_child_shows_below_its_parent_and_parent_is_no_leaf(client):
    parent_id = add_node(client, "Clocking")
    child_id = add_node(client, "PLL", parent_id=parent_id)

    page = outline(client)
    ids = [row_id for row_id, _ in page.rows]

    assert ids.index(child_id) > ids.index(parent_id)
    assert (parent_id, False) in page.rows
    assert (child_id, True) in page.rows


def test_fr_30_rename_and_describe_a_node(client):
    node_id = add_node(client, "Old name")

    response = client.post(
        f"/skill-tree/nodes/{node_id}",
        data={"name": "New name", "description": "Loop design for phase locking"},
        follow_redirects=False,
    )
    page = read_page(client.get(f"/skill-tree/{node_id}").text)

    assert response.status_code == 303
    assert response.headers["location"] == f"/skill-tree/{node_id}"
    assert "New name" in page.page_text
    assert "Loop design for phase locking" in page.page_text
    assert "Old name" not in page.page_text


def test_fr_30_delete_a_leaf_removes_it_from_the_outline(client):
    keep_id = add_node(client, "Verification")
    gone_id = add_node(client, "Emulation")

    response = client.post(f"/skill-tree/nodes/{gone_id}/delete", follow_redirects=False)
    page = outline(client)
    ids = [row_id for row_id, _ in page.rows]

    assert response.status_code == 303
    assert response.headers["location"] == "/skill-tree"
    assert gone_id not in ids
    assert keep_id in ids


def test_fr_33_delete_a_node_with_children_is_refused_with_a_message(client):
    parent_id = add_node(client, "Physical design")
    child_id = add_node(client, "Floorplanning", parent_id=parent_id)

    response = client.post(f"/skill-tree/nodes/{parent_id}/delete", follow_redirects=False)
    page = read_page(response.text)
    ids = [row_id for row_id, _ in outline(client).rows]

    assert response.status_code == 422
    assert page.alerts >= 1
    assert parent_id in ids
    assert child_id in ids
