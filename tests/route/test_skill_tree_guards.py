"""Route tests of the tree guards and the node views (M8): FR-12, FR-13, FR-33 and FR-34."""

from html.parser import HTMLParser


class TreePage(HTMLParser):
    """Collects the alerts, the outline rows, and the levels of each engineer row of a page."""

    def __init__(self):
        """Start with nothing collected."""
        super().__init__()
        self.alerts = 0
        self.node_rows: list[tuple[str, bool]] = []
        self.engineer_ids: list[str] = []
        self.levels: dict[str, dict[str, int]] = {}
        self._current_engineer = None

    def handle_starttag(self, tag, attrs):
        """Keep each alert, outline row, engineer row, and level marker that follows an engineer row."""
        attributes = dict(attrs)
        if attributes.get("role") == "alert":
            self.alerts += 1
        if "data-node-id" in attributes:
            self.node_rows.append((attributes["data-node-id"], attributes.get("data-leaf") == "true"))
        if "data-engineer-id" in attributes:
            self._current_engineer = attributes["data-engineer-id"]
            if self._current_engineer not in self.engineer_ids:
                self.engineer_ids.append(self._current_engineer)
            self.levels.setdefault(self._current_engineer, {})
        if (
            self._current_engineer
            and "data-leaf-id" in attributes
            and "data-level" in attributes
        ):
            self.levels[self._current_engineer][attributes["data-leaf-id"]] = int(
                attributes["data-level"]
            )


def read_page(response) -> TreePage:
    """Parse the HTML of a response."""
    page = TreePage()
    page.feed(response.text)
    return page


def add_node(client, name, parent_id=""):
    """Post a new node and return its ID."""
    response = client.post(
        "/skill-tree/nodes",
        data={"parent_id": parent_id, "name": name, "description": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def post_node_under(client, parent_id, name):
    """Post a new node under a parent and return the response, without following redirects."""
    return client.post(
        "/skill-tree/nodes",
        data={"parent_id": parent_id, "name": name, "description": ""},
        follow_redirects=False,
    )


def add_engineer(client, name):
    """Post a new engineer and return its ID."""
    response = client.post(
        "/engineers",
        data={
            "name": name,
            "job_title": "Design Engineer",
            "career_level": "Senior",
            "team": "Analog",
            "skill_gaps": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_project(client, name="Invented SerDes"):
    """Post a new project and return its ID."""
    response = client.post(
        "/projects",
        data={"name": name, "description": "An invented chip", "year": "2024", "process_technology": "7nm"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_assignment(client, project_id, engineer_id, leaf_id, participation):
    """Post a new assignment and check that it is accepted."""
    response = client.post(
        f"/projects/{project_id}/assignments",
        data={
            "engineer_id": engineer_id,
            "leaf_id": leaf_id,
            "participation": participation,
            "description": "Did it",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def set_flag(client, engineer_id, leaf_id, flag):
    """Post a flag and check that it is accepted."""
    response = client.post(
        f"/engineers/{engineer_id}/flags",
        data={"leaf_id": leaf_id, "flag": flag},
        follow_redirects=False,
    )
    assert response.status_code == 303


def outline_rows(client):
    """Return the outline rows (node ID, is leaf) of the Skill tree page."""
    response = client.get("/skill-tree")
    assert response.status_code == 200
    return read_page(response).node_rows


def test_fr_33_delete_a_leaf_with_an_assignment_is_refused_with_a_message(client):
    leaf_id = add_node(client, "PLL")
    engineer_id = add_engineer(client, "Ada Invented")
    add_assignment(client, add_project(client), engineer_id, leaf_id, "lead")

    response = client.post(f"/skill-tree/nodes/{leaf_id}/delete", follow_redirects=False)

    assert response.status_code == 422
    assert read_page(response).alerts >= 1
    assert (leaf_id, True) in outline_rows(client)


def test_fr_33_delete_a_leaf_with_a_flag_is_refused_with_a_message(client):
    leaf_id = add_node(client, "CDR")
    engineer_id = add_engineer(client, "Bo Invented")
    set_flag(client, engineer_id, leaf_id, "expert")

    response = client.post(f"/skill-tree/nodes/{leaf_id}/delete", follow_redirects=False)

    assert response.status_code == 422
    assert read_page(response).alerts >= 1
    assert (leaf_id, True) in outline_rows(client)


def test_fr_34_add_child_to_a_leaf_with_an_assignment_is_refused_with_a_message(client):
    leaf_id = add_node(client, "PLL")
    engineer_id = add_engineer(client, "Ada Invented")
    add_assignment(client, add_project(client), engineer_id, leaf_id, "member")

    response = post_node_under(client, leaf_id, "Charge pump")

    assert response.status_code == 422
    assert read_page(response).alerts >= 1
    assert outline_rows(client) == [(leaf_id, True)]


def test_fr_34_add_child_to_a_leaf_with_a_flag_is_refused_with_a_message(client):
    leaf_id = add_node(client, "CDR")
    engineer_id = add_engineer(client, "Bo Invented")
    set_flag(client, engineer_id, leaf_id, "aware")

    response = post_node_under(client, leaf_id, "Phase detector")

    assert response.status_code == 422
    assert read_page(response).alerts >= 1
    assert outline_rows(client) == [(leaf_id, True)]


def test_fr_12_leaf_lists_its_engineers_highest_level_first(client):
    leaf_id = add_node(client, "PLL")
    other_leaf_id = add_node(client, "VCO")
    project_id = add_project(client)
    member = add_engineer(client, "Member Invented")
    lead = add_engineer(client, "Lead Invented")
    expert = add_engineer(client, "Expert Invented")
    aware = add_engineer(client, "Aware Invented")
    unrelated = add_engineer(client, "Unrelated Invented")
    add_assignment(client, project_id, member, leaf_id, "member")
    add_assignment(client, project_id, lead, leaf_id, "lead")
    set_flag(client, expert, leaf_id, "expert")
    set_flag(client, aware, leaf_id, "aware")
    add_assignment(client, project_id, unrelated, other_leaf_id, "lead")

    response = client.get(f"/skill-tree/{leaf_id}")
    page = read_page(response)

    assert response.status_code == 200
    assert page.engineer_ids == [expert, lead, member, aware]
    assert [page.levels[e][leaf_id] for e in page.engineer_ids] == [5, 3, 2, 1]


def test_fr_13_node_lists_engineers_with_their_level_in_each_leaf_below(client):
    node_id = add_node(client, "Clocking")
    pll_id = add_node(client, "PLL", parent_id=node_id)
    vco_id = add_node(client, "VCO", parent_id=node_id)
    outside_id = add_node(client, "Verification")
    project_id = add_project(client)
    both = add_engineer(client, "Both Invented")
    expert = add_engineer(client, "Expert Invented")
    outside = add_engineer(client, "Outside Invented")
    add_assignment(client, project_id, both, pll_id, "lead")
    add_assignment(client, project_id, both, vco_id, "member")
    set_flag(client, expert, vco_id, "expert")
    add_assignment(client, project_id, outside, outside_id, "lead")

    response = client.get(f"/skill-tree/{node_id}")
    page = read_page(response)

    assert response.status_code == 200
    assert set(page.engineer_ids) == {both, expert}
    assert page.levels[both][pll_id] == 3
    assert page.levels[both][vco_id] == 2
    assert page.levels[expert][vco_id] == 5
    assert page.levels[expert].get(pll_id, 0) == 0
