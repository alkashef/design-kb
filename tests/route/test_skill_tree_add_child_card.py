"""Route test of the add-child card of the Skill tree page (M19): NFR-01 and D-19."""

from html.parser import HTMLParser

ADD_NODE_ACTION = "/skill-tree/nodes"
ADD_CHILD_LABEL = "Add child"
PANEL_CLASS = "panel"


class ControlCollector(HTMLParser):
    """Records, for the add-child form, the panels that enclose its text box and its button."""

    def __init__(self):
        """Start with an empty element stack and no controls."""
        super().__init__()
        self._stack: list[tuple[str, frozenset[str], int]] = []
        self._next_index = 0
        self._add_form_depth: int | None = None
        self._button_index: int | None = None
        self._button_text: list[str] = []
        self.text_box_panels: set[int] | None = None
        self.button_panels: set[int] | None = None

    def _panels_here(self) -> set[int]:
        """Return the indexes of the open elements that have the panel class."""
        return {index for _, classes, index in self._stack if PANEL_CLASS in classes}

    def handle_starttag(self, tag, attrs):
        """Track open elements and record the add-child text box and its button."""
        attributes = dict(attrs)
        classes = frozenset((attributes.get("class") or "").split())
        index = self._next_index
        self._next_index += 1
        if tag == "form" and attributes.get("action") == ADD_NODE_ACTION:
            self._add_form_depth = len(self._stack)
        in_add_form = self._add_form_depth is not None
        if tag == "input" and in_add_form and attributes.get("name") == "name":
            self.text_box_panels = self._panels_here()
        if tag == "button" and in_add_form:
            self._button_index = index
            self._button_text = []
        if tag not in {"input", "br", "img", "meta", "link", "hr"}:
            self._stack.append((tag, classes, index))

    def handle_data(self, data):
        """Keep the text of the open add-child button."""
        if self._button_index is not None:
            self._button_text.append(data)

    def handle_endtag(self, tag):
        """Close the element, and finish the button when its text is complete."""
        if tag == "button" and self._button_index is not None:
            if " ".join("".join(self._button_text).split()) == ADD_CHILD_LABEL:
                self.button_panels = self._panels_here()
            self._button_index = None
        for position in range(len(self._stack) - 1, -1, -1):
            if self._stack[position][0] == tag:
                del self._stack[position:]
                break
        if self._add_form_depth is not None and len(self._stack) <= self._add_form_depth:
            self._add_form_depth = None


def add_node(client, name):
    """Post a top-level node and return its ID, taken from the redirect address."""
    response = client.post(
        ADD_NODE_ACTION,
        data={"parent_id": "", "name": name, "description": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def test_nfr_01_add_child_form_is_in_a_card(client):
    """On a selected node, the Add child text box and button sit inside one panel card."""
    node_id = add_node(client, "Clocking")

    response = client.get(f"/skill-tree/{node_id}")

    assert response.status_code == 200
    collector = ControlCollector()
    collector.feed(response.text)
    assert collector.text_box_panels is not None, "no add-child text box on the page"
    assert collector.button_panels is not None, "no Add child button on the page"
    assert collector.text_box_panels & collector.button_panels, (
        "the Add child text box and button are not inside the same panel card"
    )
