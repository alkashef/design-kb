"""Helpers of the search route tests: build invented data through the routes and read the HTML.

The data is made through the routes of docs/design.md (Routes), so the vectors are made by the
app with the fake embedder. The HTML is read by the markers of docs/design.md (HTML markers).
"""

from html.parser import HTMLParser

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source"}
TREE_TOP_NAME = "Circuit design"
TREE_BRANCH_NAME = "Clocking"


def created_id(response) -> str:
    """Check that a POST redirected, and return the last part of the address it redirects to."""
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_node(client, name, description="", parent_id="") -> str:
    """Post a new skill tree node and return its ID."""
    response = client.post(
        "/skill-tree/nodes",
        data={"parent_id": parent_id, "name": name, "description": description},
        follow_redirects=False,
    )
    return created_id(response)


def add_leaves(client, descriptions: dict[str, str]) -> dict[str, str]:
    """Add the leaves (name -> description) under Circuit design / Clocking; return name -> ID."""
    top_id = add_node(client, TREE_TOP_NAME)
    branch_id = add_node(client, TREE_BRANCH_NAME, parent_id=top_id)
    return {
        name: add_node(client, name, description=description, parent_id=branch_id)
        for name, description in descriptions.items()
    }


def add_engineer(client, name, job_title="Design Engineer", team="Analog", skill_gaps="") -> str:
    """Post a new engineer and return its ID."""
    response = client.post(
        "/engineers",
        data={
            "name": name,
            "job_title": job_title,
            "career_level": "Senior",
            "team": team,
            "skill_gaps": skill_gaps,
        },
        follow_redirects=False,
    )
    return created_id(response)


def add_project(client, name="Invented SerDes", process_technology="TSMC 7nm") -> str:
    """Post a new project and return its ID."""
    response = client.post(
        "/projects",
        data={
            "name": name,
            "description": "An invented test chip",
            "year": "2024",
            "process_technology": process_technology,
        },
        follow_redirects=False,
    )
    return created_id(response)


def add_assignment(client, project_id, engineer_id, leaf_id, description, participation="lead"):
    """Post a new assignment of a project and check the redirect."""
    response = client.post(
        f"/projects/{project_id}/assignments",
        data={
            "engineer_id": engineer_id,
            "leaf_id": leaf_id,
            "participation": participation,
            "description": description,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


class Element:
    """One HTML element with its attributes, its children and its text."""

    def __init__(self, tag, attrs):
        """Make an element of the given tag with the given attributes (a dict)."""
        self.tag = tag
        self.attrs = attrs
        self.children: list["Element"] = []
        self.parts: list = []

    def descendants(self):
        """Yield every element below this one, parents before their children."""
        for child in self.children:
            yield child
            yield from child.descendants()

    def text(self) -> str:
        """Return the text of the element and its children, with white space made single."""
        pieces = []
        for part in self.parts:
            pieces.append(part.text() if isinstance(part, Element) else part)
        return " ".join("".join(pieces).replace("\xa0", " ").split())


class _TreeBuilder(HTMLParser):
    """Builds the Element tree of an HTML text."""

    def __init__(self):
        """Start with an empty root element."""
        super().__init__(convert_charrefs=True)
        self.root = Element("root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        """Open an element, and close it at once when it is a void tag."""
        element = Element(tag, {name: value or "" for name, value in attrs})
        self.stack[-1].children.append(element)
        self.stack[-1].parts.append(element)
        if tag not in VOID_TAGS:
            self.stack.append(element)

    def handle_endtag(self, tag):
        """Close the nearest open element of that tag."""
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        """Add text to the open element."""
        self.stack[-1].parts.append(data)


def parse(html: str) -> Element:
    """Return the root element of an HTML text."""
    builder = _TreeBuilder()
    builder.feed(html)
    return builder.root


def _has_reason(element: Element) -> bool:
    """Return True when the element or one below it has the marker data-reason."""
    return "data-reason" in element.attrs or any(
        "data-reason" in child.attrs for child in element.descendants()
    )


def result_rows(html: str) -> list[Element]:
    """Return the search results in page order: the data-engineer-id elements with a data-reason."""
    root = parse(html)
    return [
        element
        for element in root.descendants()
        if "data-engineer-id" in element.attrs and _has_reason(element)
    ]


def result_ids(html: str) -> list[str]:
    """Return the engineer IDs of the search results in page order."""
    return [row.attrs["data-engineer-id"] for row in result_rows(html)]


def row_of(html: str, engineer_id: str) -> Element:
    """Return the search result of one engineer."""
    rows = [row for row in result_rows(html) if row.attrs["data-engineer-id"] == engineer_id]
    assert len(rows) == 1
    return rows[0]


def reason_of(row: Element) -> str:
    """Return the text of the reason (data-reason) of a search result."""
    reasons = [
        element
        for element in [row, *row.descendants()]
        if "data-reason" in element.attrs
    ]
    assert len(reasons) == 1
    return reasons[0].text()


def leaf_tags(row: Element) -> list[Element]:
    """Return the leaf tags of a search result: the elements with data-leaf-id."""
    return [element for element in row.descendants() if "data-leaf-id" in element.attrs]


def result_count(html: str) -> str:
    """Return the value of the marker data-result-count of the page."""
    counts = [
        element.attrs["data-result-count"]
        for element in parse(html).descendants()
        if "data-result-count" in element.attrs
    ]
    assert len(counts) == 1
    return counts[0]


def page_text(html: str) -> str:
    """Return the text of the whole page, with white space made single."""
    return parse(html).text()
