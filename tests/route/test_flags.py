"""Route tests of the flags and the 360 view (M7): FR-11, FR-23, FR-24, FR-26, FR-27, FR-29, FR-40, FR-41."""

from html.parser import HTMLParser

LEVEL_NAMES = {1: "Aware", 2: "Hands-on", 3: "Lead", 4: "Senior lead", 5: "Expert"}


class ProfilePage(HTMLParser):
    """Collects the levels per leaf, the alerts, the leaf options and the assignment rows of a page."""

    def __init__(self):
        """Start with nothing collected."""
        super().__init__()
        self.levels: dict[str, int] = {}
        self.leaf_options: list[str] = []
        self.assignment_ids: list[str] = []
        self.alerts = 0
        self._in_leaf_select = False

    def handle_starttag(self, tag, attrs):
        """Keep each level marker, each assignment row, each alert and each option of a leaf list."""
        attributes = dict(attrs)
        if "data-leaf-id" in attributes and "data-level" in attributes:
            self.levels[attributes["data-leaf-id"]] = int(attributes["data-level"])
        if "data-assignment-id" in attributes:
            self.assignment_ids.append(attributes["data-assignment-id"])
        if attributes.get("role") == "alert":
            self.alerts += 1
        if tag == "select" and attributes.get("name") == "leaf_id":
            self._in_leaf_select = True
        if tag == "option" and self._in_leaf_select and attributes.get("value"):
            self.leaf_options.append(attributes["value"])

    def handle_endtag(self, tag):
        """Leave the leaf list at the end of the select."""
        if tag == "select":
            self._in_leaf_select = False


def read_page(response) -> ProfilePage:
    """Parse the HTML of a response."""
    page = ProfilePage()
    page.feed(response.text)
    return page


def add_node(client, name, parent_id=""):
    """Post a new skill tree node and return its ID."""
    response = client.post(
        "/skill-tree/nodes",
        data={"parent_id": parent_id, "name": name, "description": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_employee(client, name="Ada Invented", **extra):
    """Post a new employee and return its ID."""
    fields = {
        "name": name,
        "job_title": "Design Engineer",
        "career_level": "Senior",
        "team": "Analog",
        "skill_gaps": "",
    }
    fields.update(extra)
    response = client.post("/employees", data=fields, follow_redirects=False)
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_project(client, name="Invented SerDes", year="2024", process_technology="7nm"):
    """Post a new project and return its ID."""
    fields = {
        "name": name,
        "description": "An invented test chip",
        "year": year,
        "process_technology": process_technology,
    }
    response = client.post("/projects", data=fields, follow_redirects=False)
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_assignment(client, project_id, employee_id, leaf_id, participation, description="Did it"):
    """Post a new assignment and check that it is accepted."""
    response = client.post(
        f"/projects/{project_id}/assignments",
        data={
            "employee_id": employee_id,
            "leaf_id": leaf_id,
            "participation": participation,
            "description": description,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def post_flag(client, employee_id, leaf_id, flag):
    """Post a flag and return the response, without following redirects."""
    return client.post(
        f"/employees/{employee_id}/flags",
        data={"leaf_id": leaf_id, "flag": flag},
        follow_redirects=False,
    )


def set_flag(client, employee_id, leaf_id, flag):
    """Post a flag, check that it is accepted and goes back to the Edit employee page."""
    response = post_flag(client, employee_id, leaf_id, flag)
    assert response.status_code == 303
    assert response.headers["location"] == f"/employees/{employee_id}/edit"


def profile(client, employee_id) -> ProfilePage:
    """Return the parsed profile page of an employee."""
    response = client.get(f"/employees/{employee_id}")
    assert response.status_code == 200
    return read_page(response)


def test_fr_23_expert_flag_shows_level_5_on_the_profile(client):
    leaf_id = add_node(client, "Loop filter")
    employee_id = add_employee(client)

    set_flag(client, employee_id, leaf_id, "expert")

    assert profile(client, employee_id).levels[leaf_id] == 5


def test_fr_23_aware_flag_shows_level_1_on_the_profile(client):
    leaf_id = add_node(client, "RF front end")
    employee_id = add_employee(client)

    set_flag(client, employee_id, leaf_id, "aware")

    assert profile(client, employee_id).levels[leaf_id] == 1


def test_fr_23_removed_flag_removes_the_level(client):
    leaf_id = add_node(client, "RF front end")
    employee_id = add_employee(client)
    set_flag(client, employee_id, leaf_id, "aware")

    response = client.post(
        f"/employees/{employee_id}/flags/{leaf_id}/delete", follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/employees/{employee_id}/edit"
    assert profile(client, employee_id).levels[leaf_id] == 0


def test_fr_24_aware_flag_on_a_leaf_with_an_assignment_is_rejected_with_a_message(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client)
    project_id = add_project(client)
    add_assignment(client, project_id, employee_id, leaf_id, "member")

    response = post_flag(client, employee_id, leaf_id, "aware")

    assert response.status_code == 422
    assert read_page(response).alerts >= 1
    assert profile(client, employee_id).levels[leaf_id] == 2
    # The flag is not stored: without the assignment the leaf has no level.
    row_id = profile(client, employee_id).assignment_ids[0]
    assert client.post(f"/assignments/{row_id}/delete", follow_redirects=False).status_code == 303
    assert profile(client, employee_id).levels[leaf_id] == 0


def test_fr_26_flag_value_other_than_aware_or_expert_is_rejected(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client)

    for value in ("2", "3", "4", "hands-on", "lead", "senior lead"):
        response = post_flag(client, employee_id, leaf_id, value)
        assert response.status_code == 422, value
        assert read_page(response).alerts >= 1, value

    assert profile(client, employee_id).levels[leaf_id] == 0


def test_fr_27_expert_flag_shows_level_5_over_the_computed_level(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client)
    project_id = add_project(client)
    add_assignment(client, project_id, employee_id, leaf_id, "lead")
    assert profile(client, employee_id).levels[leaf_id] == 3

    set_flag(client, employee_id, leaf_id, "expert")

    assert profile(client, employee_id).levels[leaf_id] == 5


def test_fr_11_profile_shows_attributes_the_level_of_every_leaf_and_the_assignments(client):
    parent_id = add_node(client, "Clocking")
    pll_id = add_node(client, "PLL", parent_id=parent_id)
    vco_id = add_node(client, "VCO", parent_id=parent_id)
    cdr_id = add_node(client, "CDR", parent_id=parent_id)
    top_leaf_id = add_node(client, "Verification")
    employee_id = add_employee(
        client, name="Cy Invented", team="Mixed-signal", skill_gaps="Needs layout practice"
    )
    project_id = add_project(client, name="Invented Radar", year="2023", process_technology="5nm")
    add_assignment(client, project_id, employee_id, pll_id, "lead", "Designed the invented divider")
    add_assignment(client, project_id, employee_id, vco_id, "member", "Tuned the invented ring")
    set_flag(client, employee_id, cdr_id, "expert")

    response = client.get(f"/employees/{employee_id}")
    page = read_page(response)

    for text in (
        employee_id, "Cy Invented", "Design Engineer", "Senior", "Mixed-signal",
        "Needs layout practice", "Invented Radar", "2023", "5nm",
        "Designed the invented divider", "Tuned the invented ring",
    ):
        assert text in response.text
    assert page.levels == {pll_id: 3, vco_id: 2, cdr_id: 5, top_leaf_id: 0}
    assert len(page.assignment_ids) == 2
    for name in (LEVEL_NAMES[3], LEVEL_NAMES[2], LEVEL_NAMES[5]):
        assert name in response.text


def test_fr_29_delete_employee_deletes_its_flags(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client, name="Gone Invented")
    set_flag(client, employee_id, leaf_id, "expert")

    response = client.post(f"/employees/{employee_id}/delete", follow_redirects=False)

    assert response.status_code == 303
    assert post_flag(client, employee_id, leaf_id, "aware").status_code == 404
    # On an empty store the next free ID is the one that was freed (D-25), so a stale flag would show.
    new_employee_id = add_employee(client, name="New Invented")
    assert new_employee_id == employee_id
    assert profile(client, new_employee_id).levels[leaf_id] == 0


def test_fr_40_flag_form_lists_only_leaves(client):
    parent_id = add_node(client, "Clocking")
    pll_id = add_node(client, "PLL", parent_id=parent_id)
    cdr_id = add_node(client, "CDR", parent_id=parent_id)
    top_leaf_id = add_node(client, "Verification")
    employee_id = add_employee(client)

    response = client.get(f"/employees/{employee_id}/edit")

    assert response.status_code == 200
    options = set(read_page(response).leaf_options)
    assert options == {pll_id, cdr_id, top_leaf_id}
    assert parent_id not in options


def test_fr_41_flag_on_a_node_with_children_is_rejected_with_a_message(client):
    parent_id = add_node(client, "Clocking")
    leaf_id = add_node(client, "PLL", parent_id=parent_id)
    employee_id = add_employee(client)

    for flag in ("aware", "expert"):
        response = post_flag(client, employee_id, parent_id, flag)
        assert response.status_code == 422, flag
        assert read_page(response).alerts >= 1, flag

    levels = profile(client, employee_id).levels
    assert levels == {leaf_id: 0}
